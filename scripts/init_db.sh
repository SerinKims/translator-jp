#!/usr/bin/env bash
set -euo pipefail

sqlite3 backend/translation.db < backend/app/db/schema.sql
