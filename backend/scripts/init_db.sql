-- 校事通 数据库初始化脚本
-- 使用前请先创建数据库：
-- CREATE DATABASE compusmind;

-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    user_id         SERIAL PRIMARY KEY,
    username        VARCHAR(50) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    name            VARCHAR(50) NOT NULL,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('super_admin', 'admin', 'teacher', 'student')),
    department      VARCHAR(100) NOT NULL,
    education_level VARCHAR(10) DEFAULT NULL,
    grade           VARCHAR(10) DEFAULT NULL,
    admin_scope     VARCHAR(100) DEFAULT NULL,
    school_id       VARCHAR(20) DEFAULT NULL,
    email           VARCHAR(100) DEFAULT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    is_first_login  BOOLEAN DEFAULT TRUE,
    login_attempts  INT DEFAULT 0,
    locked_until    TIMESTAMPTZ DEFAULT NULL,
    last_login      TIMESTAMPTZ DEFAULT NULL,
    delegate_to     INT DEFAULT NULL REFERENCES users(user_id),
    delegate_until  TIMESTAMPTZ DEFAULT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_department ON users(department);

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id          SERIAL PRIMARY KEY,
    operator_id     INT NOT NULL REFERENCES users(user_id),
    operator_name   VARCHAR(50) NOT NULL,
    action          VARCHAR(50) NOT NULL,
    resource_type   VARCHAR(50) NOT NULL,
    resource_id     INT DEFAULT NULL,
    detail          JSONB DEFAULT NULL,
    ip_address      VARCHAR(45) DEFAULT NULL,
    user_agent      VARCHAR(500) DEFAULT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_operator ON audit_logs(operator_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id);