# PostgreSQL Dockerfile

这个 Dockerfile 基于 `postgres:16-alpine` 镜像构建。

## 自定义配置

如果需要自定义 PostgreSQL 配置，可以：

1. **添加初始化脚本**：
   - 在 `database/init-scripts/` 目录下创建 SQL 脚本
   - 这些脚本会在数据库首次初始化时自动执行
   - 取消 Dockerfile 中的注释以启用

2. **自定义 postgresql.conf**：
   - 创建 `database/postgresql.conf` 文件
   - 取消 Dockerfile 中的注释以使用自定义配置

## 示例初始化脚本

如果需要创建数据库扩展或执行初始化 SQL，可以在 `database/init-scripts/` 目录下创建 `.sql` 文件。

例如：`database/init-scripts/01-extensions.sql`
```sql
-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

