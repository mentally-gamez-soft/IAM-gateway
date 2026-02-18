# US-016 — Implement Automated Database Backups

## Title

Set Up Automated PostgreSQL Backup Strategy

## User Story

As a **system administrator**, I want automated daily PostgreSQL database backups with off-site storage, so that data can be recovered in case of failure.

## Description

A cron-based script should run `pg_dump` daily, compress the output, encrypt it with GPG, and upload to a remote storage (S3-compatible or SFTP). Retention policy: 7 daily, 4 weekly, 3 monthly backups. A restore procedure should be documented and tested quarterly.

### Key Requirements

- Bash script performing: `pg_dump` → `gzip` → `gpg` encrypt → upload to remote storage
- Cron job scheduled at 02:00 UTC daily
- Retention policy:
  - 7 daily backups
  - 4 weekly backups (every Sunday)
  - 3 monthly backups (first of each month)
- Automated cleanup of expired backups
- Exit code and error notification (email or webhook on failure)
- Restore procedure documented with step-by-step instructions
- Restore tested quarterly with verification checklist
- Backup file naming convention: `iam-gateway_<env>_<YYYY-MM-DD_HHMMSS>.sql.gz.gpg`

### Affected Components

- New `scripts/backup/` directory for backup and restore scripts
- New `DOCUMENTATION/BACKUP_RESTORE.md` for procedures
- Docker Compose (optional: dedicated backup container)
- VPS crontab configuration
- `.env` files for backup credentials (GPG key, storage access)

## Priority

**High**

## Estimated Cost

**3 Story Points** (~1.5 days)

## Related Tasks

- [task_016_1.md](../TASKS/task_016_1.md) — Create PostgreSQL backup script
- [task_016_2.md](../TASKS/task_016_2.md) — Implement encryption and remote upload
- [task_016_3.md](../TASKS/task_016_3.md) — Implement retention policy and cleanup
- [task_016_4.md](../TASKS/task_016_4.md) — Create restore procedure and documentation
- [task_016_5.md](../TASKS/task_016_5.md) — Set up cron job and failure notifications

## Trello

[US-016 — Automated Database Backup Strategy](https://trello.com/c/Q6LC0UBS)
