-- MySQL：为 items.status 枚举增加 offline（已下架）。请在备份后执行。
ALTER TABLE items
  MODIFY COLUMN status ENUM('pending', 'matched', 'claimed', 'expired', 'offline')
  NOT NULL DEFAULT 'pending';
