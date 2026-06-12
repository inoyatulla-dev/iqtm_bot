#!/bin/bash
# IQTM — serverda joylashtirish: eski kodni to'xtatib, yangisini ishga tushiradi.
# Ishlatish: serverda ushbu faylni yarating (masalan nano deploy_server.sh), so'ng:
#   chmod +x deploy_server.sh && sudo ./deploy_server.sh
set -e

echo "############################################################"
echo "# [1] Loyiha papkasini qidirish..."
echo "############################################################"
PROJECT_DIR=$(find / -maxdepth 4 -iname "iqtm*" -type d 2>/dev/null | grep -v node_modules | grep -v .git | head -1)
echo "Topildi: ${PROJECT_DIR:-<TOPILMADI>}"
if [ -z "$PROJECT_DIR" ]; then
  echo "XATO: loyiha papkasi avtomatik topilmadi. Qo'lda PROJECT_DIR= belgilab qayta ishga tushiring."
  exit 1
fi

echo
echo "############################################################"
echo "# [2] Hozir ishlayotgan eski jarayon/xizmatlarni aniqlash..."
echo "############################################################"
OLD_PROCS=$(ps aux | grep -iE "uvicorn|gunicorn|app\.bot\.run|app\.main|vite" | grep -v grep || true)
echo "--- Jarayonlar ---"
echo "${OLD_PROCS:-<topilmadi>}"

SERVICES=$(systemctl list-units --type=service --all 2>/dev/null | grep -iE "iqtm" | awk '{print $1}' || true)
echo "--- systemd xizmatlari ---"
echo "${SERVICES:-<topilmadi>}"

echo
echo "Yuqoridagilar TO'XTATILADI, so'ng yangi kod bilan QAYTA ISHGA TUSHIRILADI."
read -p "Davom etamizmi? (ha/yo'q): " CONFIRM
if [ "$CONFIRM" != "ha" ]; then
  echo "Bekor qilindi — hech narsa o'zgartirilmadi."
  exit 0
fi

echo
echo "############################################################"
echo "# [3] Eski kodni to'xtatish..."
echo "############################################################"
if [ -n "$SERVICES" ]; then
  for s in $SERVICES; do
    echo "  -> systemctl stop $s"
    systemctl stop "$s" || true
  done
else
  echo "$OLD_PROCS" | awk '{print $2}' | while read -r pid; do
    if [ -n "$pid" ]; then
      echo "  -> kill $pid"
      kill "$pid" 2>/dev/null || true
    fi
  done
  sleep 2
fi

echo
echo "############################################################"
echo "# [3.5] Bazani zaxiralash (deploy oldidan xavfsizlik nusxasi)..."
echo "############################################################"
BACKUP_DIR="$PROJECT_DIR/backend/backups"
mkdir -p "$BACKUP_DIR"
DB_FILE=$(find "$PROJECT_DIR/backend" -maxdepth 1 -iname "*.db" | head -1)
if [ -n "$DB_FILE" ]; then
  STAMP=$(date +%Y%m%d_%H%M%S)
  cp "$DB_FILE" "$BACKUP_DIR/$(basename "$DB_FILE" .db)_deploy_${STAMP}.db"
  echo "  -> Zaxira: $BACKUP_DIR/$(basename "$DB_FILE" .db)_deploy_${STAMP}.db"
  # Faqat oxirgi 10 ta deploy-zaxira saqlanadi
  ls -1t "$BACKUP_DIR"/*_deploy_*.db 2>/dev/null | tail -n +11 | xargs -r rm -f
else
  echo "  -> Baza fayli topilmadi (birinchi ishga tushirish bo'lishi mumkin) — o'tkazib yuborildi"
fi

echo
echo "############################################################"
echo "# [4] Yangi kodni olish (git pull)..."
echo "############################################################"
cd "$PROJECT_DIR"
git pull

echo
echo "############################################################"
echo "# [5] Backend: kutubxonalar + migratsiya..."
echo "############################################################"
cd "$PROJECT_DIR/backend"
VENV_DIR=""
for v in venv .venv env; do [ -d "$v" ] && VENV_DIR="$v" && break; done
echo "venv: ${VENV_DIR:-<topilmadi, tizim python ishlatiladi>}"
if [ -n "$VENV_DIR" ]; then
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
fi
pip install -r requirements.txt -q
if [ -d alembic ]; then
  echo "Alembic migratsiya..."
  alembic upgrade head || echo "  (alembic upgrade muvaffaqiyatsiz — qo'lda tekshiring)"
fi

echo
echo "############################################################"
echo "# [6] Frontend qurish (npm run build)..."
echo "############################################################"
cd "$PROJECT_DIR/frontend"
npm install --no-audit --no-fund
npm run build
echo "Build natijasi: $PROJECT_DIR/frontend/dist"
echo "ESLATMA: agar nginx static fayllarni boshqa joydan bersa, dist/ ni o'sha joyga ko'chiring."

echo
echo "############################################################"
echo "# [7] Yangi kodni ishga tushirish..."
echo "############################################################"
if [ -n "$SERVICES" ]; then
  for s in $SERVICES; do
    echo "  -> systemctl start $s"
    systemctl start "$s"
    sleep 1
    systemctl --no-pager --lines=4 status "$s" || true
  done
else
  cd "$PROJECT_DIR/backend"
  [ -n "$VENV_DIR" ] && source "$VENV_DIR/bin/activate"
  nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$PROJECT_DIR/uvicorn.log" 2>&1 &
  echo "  uvicorn PID: $!"
  nohup python -m app.bot.run > "$PROJECT_DIR/bot.log" 2>&1 &
  echo "  bot PID: $!"
fi

echo
echo "############################################################"
echo "# TAYYOR. Loglarni tekshiring:"
echo "#   journalctl -u <xizmat-nomi> -f     (systemd bo'lsa)"
echo "#   tail -f $PROJECT_DIR/*.log          (qo'lda ishga tushirilgan bo'lsa)"
echo "############################################################"
