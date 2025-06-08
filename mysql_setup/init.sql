-- Tạo user 'polluser' chỉ với quyền SELECT
CREATE USER 'polluser'@'%' IDENTIFIED BY 'pollpassword';
GRANT SELECT ON `productiondb`.* TO 'polluser'@'%';
FLUSH PRIVILEGES;