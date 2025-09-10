-- JobFit Analytics - Full Schema (MySQL)
-- Usage: import this file into your MySQL to create all tables with full fields
-- Charset & engine
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Drop existing tables (order matters due to FK)
DROP TABLE IF EXISTS `cv`;
DROP TABLE IF EXISTS `job`;
DROP TABLE IF EXISTS `settings`;
DROP TABLE IF EXISTS `user`;

-- USER
CREATE TABLE `user` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(80) NOT NULL UNIQUE,
  `email` VARCHAR(120) NOT NULL UNIQUE,
  `password_hash` VARCHAR(120) NOT NULL,
  `is_admin` TINYINT(1) DEFAULT 0,
  `created_at` DATETIME NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- JOB
CREATE TABLE `job` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(200) NOT NULL,
  `description` TEXT NULL,
  `company` VARCHAR(200) NULL,
  `location` VARCHAR(200) NULL,
  `salary_min` DECIMAL(10,2) NULL,
  `salary_max` DECIMAL(10,2) NULL,
  `employment_type` VARCHAR(50) NULL,
  `requirements` TEXT NULL,
  `benefits` TEXT NULL,
  `application_deadline` DATETIME NULL,
  `hiring_quantity` INT NULL DEFAULT 1,
  `experience_level` VARCHAR(50) NULL,
  `work_mode` VARCHAR(50) NULL,
  `industry` VARCHAR(100) NULL,
  `skills_required` TEXT NULL,
  `education_required` VARCHAR(100) NULL,
  `is_active` TINYINT(1) DEFAULT 1,
  `user_id` INT NULL,
  `created_at` DATETIME NULL,
  `updated_at` DATETIME NULL,

  -- Matching Criteria (JD-side, 13 fields)
  `criteria_seniority` VARCHAR(50) NULL,
  `criteria_core_skills` TEXT NULL,
  `criteria_language` VARCHAR(100) NULL,
  `criteria_work_model` VARCHAR(50) NULL,
  `criteria_visa_required` TINYINT(1) NULL,
  `criteria_secondary_skills` TEXT NULL,
  `criteria_years_experience` INT NULL,
  `criteria_recency_years` INT NULL,
  `criteria_domain` VARCHAR(100) NULL,
  `criteria_kpi_required` TINYINT(1) NULL,
  `criteria_stack_versions` TEXT NULL,
  `criteria_soft_skills` TEXT NULL,
  `criteria_culture_process` VARCHAR(100) NULL,

  PRIMARY KEY (`id`),
  KEY `idx_job_user_id` (`user_id`),
  CONSTRAINT `fk_job_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- CV
CREATE TABLE `cv` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(120) NULL,
  `phone` VARCHAR(20) NULL,
  `address` TEXT NULL,
  `education` TEXT NULL,
  `experience` TEXT NULL,
  `skills` TEXT NULL,
  `file_path` VARCHAR(200) NULL,
  `avatar` VARCHAR(200) NULL,
  `user_id` INT NULL,
  `created_at` DATETIME NULL,
  `updated_at` DATETIME NULL,

  -- Matching Criteria (CV-side, 13 fields)
  `cv_seniority` VARCHAR(50) NULL,
  `cv_core_skills` TEXT NULL,
  `cv_languages` VARCHAR(200) NULL,
  `cv_work_model` VARCHAR(50) NULL,
  `cv_visa_status` VARCHAR(50) NULL,
  `cv_secondary_skills` TEXT NULL,
  `cv_years_experience` INT NULL,
  `cv_recency_years` INT NULL,
  `cv_domain` VARCHAR(100) NULL,
  `cv_kpi` TEXT NULL,
  `cv_stack_versions` TEXT NULL,
  `cv_soft_skills` TEXT NULL,
  `cv_culture_process` VARCHAR(100) NULL,

  PRIMARY KEY (`id`),
  KEY `idx_cv_user_id` (`user_id`),
  CONSTRAINT `fk_cv_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- SETTINGS
CREATE TABLE `settings` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `auto_extract` TINYINT(1) DEFAULT 1,
  `email_notifications` TINYINT(1) DEFAULT 1,
  `created_at` DATETIME NULL,
  `updated_at` DATETIME NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;

-- Optional seed admin (change password hash if needed)
-- INSERT INTO `user` (`username`,`email`,`password_hash`,`is_admin`,`created_at`)
-- VALUES ('admin','admin@example.com','$pbkdf2-sha256$...','1', NOW());


