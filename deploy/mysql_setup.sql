-- Einmalig als root ausführen: sudo mysql -u root -p < deploy/mysql_setup.sql
CREATE DATABASE dbwe CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'dbwe'@'localhost' IDENTIFIED BY 'GEHEIMES_PASSWORT';
GRANT ALL PRIVILEGES ON dbwe.* TO 'dbwe'@'localhost';
FLUSH PRIVILEGES;
