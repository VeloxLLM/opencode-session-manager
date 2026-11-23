use eframe::egui::{self, FontData, FontDefinitions, FontFamily, Color32, Rounding, Vec2};
use rusqlite::{params, params_from_iter, types::Value as SqlValue, Connection};
use std::path::PathBuf;
use chrono::{Local, TimeZone};
use serde_json::{json, Value};

fn main() -> eframe::Result<()> {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([1000.0, 700.0])
            .with_min_inner_size([800.0, 500.0]),
        ..Default::default()
    };

    eframe::run_native(
        "OpenCode Session Manager",
        options,
        Box::new(|cc| {
            setup_style(&cc.egui_ctx);
            setup_fonts(&cc.egui_ctx);
            Ok(Box::new(App::new(cc)))
        }),
    )
}

fn setup_style(ctx: &egui::Context) {
    let mut style = (*ctx.style()).clone();
    
    // 设置圆角
    style.visuals.window_rounding = Rounding::same(8.0);
    style.visuals.widgets.noninteractive.rounding = Rounding::same(4.0);
    style.visuals.widgets.inactive.rounding = Rounding::same(4.0);
    style.visuals.widgets.hovered.rounding = Rounding::same(4.0);
    style.visuals.widgets.active.rounding = Rounding::same(4.0);
    
    // 设置间距
    style.spacing.item_spacing = Vec2::new(8.0, 6.0);
    style.spacing.window_margin = egui::Margin::same(12.0);
    
    ctx.set_style(style);
}

fn setup_fonts(ctx: &egui::Context) {
    let mut fonts = FontDefinitions::default();
    
    // 加载 Windows 系统中文字体
    let font_paths = [
        "C:\\Windows\\Fonts\\msyh.ttc",    // 微软雅黑
        "C:\\Windows\\Fonts\\simhei.ttf",  // 黑体
        "C:\\Windows\\Fonts\\simsun.ttc",  // 宋体
    ];
    
    for font_path in &font_paths {
        if let Ok(font_data) = std::fs::read(font_path) {
            fonts.font_data.insert(
                "chinese".to_owned(),
                FontData::from_owned(font_data),
            );
            // 将中文字体添加到默认字体族
            if let Some(family) = fonts.families.get_mut(&FontFamily::Proportional) {
                family.push("chinese".to_owned());
            }
            if let Some(family) = fonts.families.get_mut(&FontFamily::Monospace) {
                family.push("chinese".to_owned());
            }
            break;
        }
    }
    
    ctx.set_fonts(fonts);
}

#[derive(Clone, Debug)]
struct Session {
    id: String,
    title: String,
    directory: String,
    project_id: String,
    version: String,
    time_created: i64,
    time_updated: i64,
    time_archived: Option<i64>,
    message_count: i64,
    cost: f64,
    tokens_input: i64,
    tokens_output: i64,
}

impl Session {
    fn tokens_total(&self) -> i64 {
        self.tokens_input + self.tokens_output
    }
}

struct App {
    lang: String,
    db_path: Option<PathBuf>,
    sessions: Vec<Session>,
    selected_sessions: Vec<usize>,
    filter_text: String,
    time_filter: String,
    status_filter: String,
    file_path: String,
    status_message: String,
    confirm_action: Option<String>,
}

impl App {
    fn new(_cc: &eframe::CreationContext<'_>) -> Self {
        let mut app = Self {
            lang: "zh".to_string(),
            db_path: find_opencode_db(),
            sessions: Vec::new(),
            selected_sessions: Vec::new(),
            filter_text: String::new(),
            time_filter: "all".to_string(),
            status_filter: "all".to_string(),
            file_path: "opencode_sessions.json".to_string(),
            status_message: "就绪".to_string(),
            confirm_action: None,
        };

        app.load_sessions();
        app
    }

    fn t(&self, key: &str) -> String {
        match self.lang.as_str() {
            "zh" => match key {
                "window_title" => "OpenCode 会话管理器".to_string(),
                "sessions" => "📋 会话".to_string(),
                "refresh" => "🔄 刷新".to_string(),
                "select_db" => "📂 选择数据库".to_string(),
                "vacuum" => "📦 压缩".to_string(),
                "export" => "💾 导出".to_string(),
                "import" => "📥 导入".to_string(),
                "delete" => "🗑️ 删除".to_string(),
                "delete_archived" => "🗑️ 删除已归档".to_string(),
                "archive_path" => "存档路径".to_string(),
                "no_selection" => "请先选择会话".to_string(),
                "no_archived" => "没有已归档的会话".to_string(),
                "confirm_archived_msg" => "确定删除全部已归档会话吗？\n此操作不可撤销！".to_string(),
                "confirm_import_msg" => "导入会写入当前数据库，重复会话将被覆盖。继续吗？".to_string(),
                "archive_saved" => "已导出 {} 个会话".to_string(),
                "import_done" => "已导入 {} 个会话、{} 条消息、{} 个片段".to_string(),
                "export_failed" => "导出失败".to_string(),
                "import_failed" => "导入失败".to_string(),
                "status_all" => "全部状态".to_string(),
                "status_active" => "活跃".to_string(),
                "status_archived" => "已归档".to_string(),
                "details" => "详情".to_string(),
                "id" => "ID".to_string(),
                "title" => "标题".to_string(),
                "version" => "版本".to_string(),
                "created" => "创建时间".to_string(),
                "directory" => "目录".to_string(),
                "messages" => "消息数".to_string(),
                "tokens" => "Token".to_string(),
                "cost" => "费用".to_string(),
                "archived_flag" => " [已归档]".to_string(),
                "select_all" => "全选".to_string(),
                "deselect_all" => "取消全选".to_string(),
                "lang_switch" => "EN".to_string(),
                "filter_placeholder" => "🔍 筛选...".to_string(),
                "time_all" => "全部时间".to_string(),
                "time_today" => "今天".to_string(),
                "time_week" => "最近7天".to_string(),
                "time_month" => "最近30天".to_string(),
                "confirm_delete" => "确认删除".to_string(),
                "confirm_import" => "确认导入".to_string(),
                "confirm_delete_msg" => "确定要删除选中的记录吗？\n此操作不可撤销！".to_string(),
                "yes" => "✓ 是".to_string(),
                "no" => "✗ 否".to_string(),
                "no_sessions" => "没有找到会话".to_string(),
                "total" => "总计".to_string(),
                "sessions_count" => "个会话".to_string(),
                "records_count" => "条记录".to_string(),
                _ => key.to_string(),
            },
            _ => match key {
                "window_title" => "OpenCode Session Manager".to_string(),
                "sessions" => "📋 Sessions".to_string(),
                "refresh" => "🔄 Refresh".to_string(),
                "select_db" => "📂 Select DB".to_string(),
                "vacuum" => "📦 Vacuum".to_string(),
                "export" => "💾 Export".to_string(),
                "import" => "📥 Import".to_string(),
                "delete" => "🗑️ Delete".to_string(),
                "delete_archived" => "🗑️ Delete Archived".to_string(),
                "archive_path" => "Archive path".to_string(),
                "no_selection" => "Please select sessions first".to_string(),
                "no_archived" => "No archived sessions found".to_string(),
                "confirm_archived_msg" => "Delete all archived sessions?\nThis cannot be undone!".to_string(),
                "confirm_import_msg" => "Import will write to the current database; duplicate sessions will be replaced. Continue?".to_string(),
                "archive_saved" => "Exported {} session(s)".to_string(),
                "import_done" => "Imported {} sessions, {} messages, {} parts".to_string(),
                "export_failed" => "Export failed".to_string(),
                "import_failed" => "Import failed".to_string(),
                "status_all" => "All status".to_string(),
                "status_active" => "Active".to_string(),
                "status_archived" => "Archived".to_string(),
                "details" => "Details".to_string(),
                "id" => "ID".to_string(),
                "title" => "Title".to_string(),
                "version" => "Version".to_string(),
                "created" => "Created".to_string(),
                "directory" => "Directory".to_string(),
                "messages" => "Messages".to_string(),
                "tokens" => "Tokens".to_string(),
                "cost" => "Cost".to_string(),
                "archived_flag" => " [A]".to_string(),
                "select_all" => "Select All".to_string(),
                "deselect_all" => "Deselect All".to_string(),
                "lang_switch" => "中文".to_string(),
                "filter_placeholder" => "🔍 Filter...".to_string(),
                "time_all" => "All Time".to_string(),
                "time_today" => "Today".to_string(),
                "time_week" => "7 Days".to_string(),
                "time_month" => "30 Days".to_string(),
                "confirm_delete" => "Confirm Delete".to_string(),
                "confirm_import" => "Confirm Import".to_string(),
                "confirm_delete_msg" => "Delete selected records?\nThis cannot be undone!".to_string(),
                "yes" => "✓ Yes".to_string(),
                "no" => "✗ No".to_string(),
                "no_sessions" => "No sessions found".to_string(),
                "total" => "Total".to_string(),
                "sessions_count" => "sessions".to_string(),
                "records_count" => "records".to_string(),
                _ => key.to_string(),
            },
        }
    }

    fn load_sessions(&mut self) {
        self.sessions.clear();

        let db_path = match &self.db_path {
            Some(p) => p.clone(),
            None => return,
        };

        let conn = match Connection::open(&db_path) {
            Ok(c) => c,
            Err(e) => {
                self.status_message = format!("数据库打开失败: {}", e);
                return;
            }
        };

        let has_v2: bool = conn
            .prepare("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'session_v2'")
            .and_then(|mut stmt| stmt.exists(params![]))
            .unwrap_or(false);
        if !has_v2 {
            self.status_message = "仅支持 OpenCode v2 数据库".to_string();
            return;
        }

        let mut stmt = match conn.prepare(
            "SELECT s.id, s.title, s.directory, s.project_id, s.version, \
             s.time_created, s.time_updated, s.time_archived, \
             s.cost, s.tokens_input, s.tokens_output, COUNT(m.id) AS message_count \
             FROM session_v2 s \
             LEFT JOIN session_message m ON m.session_id = s.id \
             GROUP BY s.id ORDER BY s.time_updated DESC",
        ) {
            Ok(s) => s,
            Err(e) => {
                self.status_message = format!("查询失败: {}", e);
                return;
            }
        };
        let rows = stmt.query_map([], |row| {
            Ok(Session {
                id: row.get(0)?,
                title: row.get::<_, Option<String>>(1)?.unwrap_or_default(),
                directory: row.get(2)?,
                project_id: row.get(3)?,
                version: row.get(4)?,
                time_created: row.get(5)?,
                time_updated: row.get(6)?,
                time_archived: row.get(7)?,
                message_count: row.get(11).unwrap_or(0),
                cost: row.get(8).unwrap_or(0.0),
                tokens_input: row.get(9).unwrap_or(0),
                tokens_output: row.get(10).unwrap_or(0),
            })
        });
        if let Ok(rows) = rows {
            for row in rows.flatten() {
                self.sessions.push(row);
            }
        }

        self.status_message = format!("{} {} 条", self.t("total"), self.sessions.len());
    }

    fn delete_selected_sessions(&mut self) {
        if self.selected_sessions.is_empty() {
            return;
        }

        let db_path = match &self.db_path {
            Some(p) => p.clone(),
            None => return,
        };

        let conn = match Connection::open(&db_path) {
            Ok(c) => c,
            Err(_) => return,
        };

        let selected_ids: Vec<String> = self.selected_sessions.iter()
            .filter_map(|&i| self.sessions.get(i).map(|s| s.id.clone()))
            .collect();

        let _ = conn.execute("PRAGMA foreign_keys = ON", params![]);
        for id in &selected_ids {
            let _ = conn.execute("DELETE FROM session_v2 WHERE id = ?", params![id.as_str()]);
        }

        self.selected_sessions.clear();
        self.load_sessions();
    }

    fn table_columns(conn: &Connection, table: &str) -> Vec<String> {
        let mut stmt = match conn.prepare(&format!("PRAGMA table_info(\"{}\")", table)) {
            Ok(stmt) => stmt,
            Err(_) => return Vec::new(),
        };
        let columns = match stmt.query_map(params![], |row| row.get::<_, String>(1)) {
            Ok(rows) => rows.flatten().collect(),
            Err(_) => Vec::new(),
        };
        columns
    }

    fn sql_to_json(value: SqlValue) -> Value {
        match value {
            SqlValue::Null => Value::Null,
            SqlValue::Integer(i) => json!(i),
            SqlValue::Real(f) => json!(f),
            SqlValue::Text(s) => json!(s),
            SqlValue::Blob(b) => json!(b),
        }
    }

    fn json_to_sql(value: &Value) -> SqlValue {
        match value {
            Value::Null => SqlValue::Null,
            Value::Bool(b) => SqlValue::Integer(if *b { 1 } else { 0 }),
            Value::Number(n) => {
                if let Some(i) = n.as_i64() {
                    SqlValue::Integer(i)
                } else if let Some(f) = n.as_f64() {
                    SqlValue::Real(f)
                } else {
                    SqlValue::Null
                }
            }
            Value::String(s) => SqlValue::Text(s.clone()),
            other => SqlValue::Text(other.to_string()),
        }
    }

    fn rows_to_json(conn: &Connection, table: &str, where_sql: &str, id: &str) -> Vec<Value> {
        let columns = Self::table_columns(conn, table);
        if columns.is_empty() {
            return Vec::new();
        }
        let order_sql = if columns.iter().any(|column| column == "seq") {
            " ORDER BY seq"
        } else if columns.iter().any(|column| column == "time_created") {
            " ORDER BY time_created"
        } else {
            ""
        };
        let sql = format!(
            "SELECT * FROM {} WHERE {} = ?{}",
            table, where_sql, order_sql
        );
        let mut stmt = match conn.prepare(&sql) {
            Ok(stmt) => stmt,
            Err(_) => return Vec::new(),
        };
        let rows = match stmt.query_map(params![id], |row| {
            let mut map = serde_json::Map::new();
            for (index, column) in columns.iter().enumerate() {
                let value: SqlValue = row.get(index)?;
                map.insert(column.clone(), Self::sql_to_json(value));
            }
            Ok(Value::Object(map))
        }) {
            Ok(rows) => rows,
            Err(_) => return Vec::new(),
        };
        rows.flatten().collect()
    }

    fn insert_row(conn: &Connection, table: &str, value: &Value, allowed: &[&str]) -> usize {
        if !allowed.contains(&table) {
            return 0;
        }
        let object = match value.as_object() {
            Some(object) => object,
            None => return 0,
        };
        let columns = Self::table_columns(conn, table);
        let mut keys: Vec<&String> = object.keys().filter(|key| columns.contains(*key)).collect();
        if keys.is_empty() {
            return 0;
        }
        keys.sort();
        let names = keys.iter().map(|key| format!("\"{}\"", key)).collect::<Vec<_>>().join(", ");
        let marks = (0..keys.len()).map(|_| "?").collect::<Vec<_>>().join(", ");
        let sql = format!("INSERT OR REPLACE INTO {} ({}) VALUES ({})", table, names, marks);
        let values: Vec<SqlValue> = keys.iter().map(|key| Self::json_to_sql(&object[*key])).collect();
        match conn.execute(&sql, params_from_iter(values)) {
            Ok(_) => 1,
            Err(_) => 0,
        }
    }

    fn export_selected(&mut self) {
        if self.selected_sessions.is_empty() {
            self.status_message = self.t("no_selection");
            return;
        }
        let db_path = match &self.db_path {
            Some(path) => path.clone(),
            None => return,
        };
        let conn = match Connection::open(&db_path) {
            Ok(conn) => conn,
            Err(e) => {
                self.status_message = format!("{}: {}", self.t("export_failed"), e);
                return;
            }
        };

        let mut exported = Vec::new();
        for &index in &self.selected_sessions {
            let session = match self.sessions.get(index) {
                Some(session) => session,
                None => continue,
            };
            let rows = Self::rows_to_json(&conn, "session_v2", "id", &session.id);
            if let Some(row) = rows.into_iter().next() {
                exported.push(json!({
                    "table": "session_v2",
                    "row": row,
                    "messages": Self::rows_to_json(&conn, "session_message", "session_id", &session.id),
                    "parts": Self::rows_to_json(&conn, "session_part", "session_id", &session.id),
                }));
            }
        }

        let payload = json!({
            "format": "opencode-session-manager",
            "version": 2,
            "created_at": Local::now().to_rfc3339(),
            "source": db_path.to_string_lossy(),
            "sessions": exported,
        });
        match serde_json::to_string_pretty(&payload)
            .map_err(|e| e.to_string())
            .and_then(|text| std::fs::write(&self.file_path, text).map_err(|e| e.to_string()))
        {
            Ok(_) => self.status_message = self.t("archive_saved").replace("{}", &exported.len().to_string()),
            Err(e) => self.status_message = format!("{}: {}", self.t("export_failed"), e),
        }
    }

    fn import_archive(&mut self) {
        let file_path = self.file_path.clone();
        let text = match std::fs::read_to_string(&file_path) {
            Ok(text) => text,
            Err(e) => {
                self.status_message = format!("{}: {}", self.t("import_failed"), e);
                return;
            }
        };
        let payload: Value = match serde_json::from_str(&text) {
            Ok(value) => value,
            Err(e) => {
                self.status_message = format!("{}: {}", self.t("import_failed"), e);
                return;
            }
        };
        if payload.get("format").and_then(|v| v.as_str()) != Some("opencode-session-manager")
            || payload.get("version").and_then(|v| v.as_i64()) != Some(2)
        {
            self.status_message = self.t("import_failed");
            return;
        }
        let sessions = match payload.get("sessions").and_then(|v| v.as_array()) {
            Some(sessions) => sessions,
            None => {
                self.status_message = self.t("import_failed");
                return;
            }
        };

        let db_path = match &self.db_path {
            Some(path) => path.clone(),
            None => return,
        };
        let conn = match Connection::open(&db_path) {
            Ok(conn) => conn,
            Err(e) => {
                self.status_message = format!("{}: {}", self.t("import_failed"), e);
                return;
            }
        };
        let was_enabled: i64 = conn
            .query_row("PRAGMA foreign_keys", params![], |row| row.get(0))
            .unwrap_or(0);
        if was_enabled == 1 {
            let _ = conn.execute("PRAGMA foreign_keys = OFF", params![]);
        }

        let mut session_count = 0;
        let mut message_count = 0;
        let mut part_count = 0;
        for item in sessions {
            if item.get("table").and_then(|v| v.as_str()) != Some("session_v2") {
                continue;
            }
            let row = match item.get("row") {
                Some(row) => row,
                None => continue,
            };
            let project_id = row.get("project_id").and_then(|v| v.as_str()).unwrap_or("");
            if !project_id.is_empty() {
                let directory = row.get("directory").and_then(|v| v.as_str()).unwrap_or("/");
                let created = row.get("time_created").and_then(|v| v.as_i64()).unwrap_or(0);
                let updated = row.get("time_updated").and_then(|v| v.as_i64()).unwrap_or(0);
                let _ = conn.execute(
                    "INSERT OR IGNORE INTO project (id, worktree, vcs, name, time_created, time_updated, sandboxes) \
                     VALUES (?, ?, NULL, NULL, ?, ?, '[]')",
                    params![project_id, directory, created, updated],
                );
            }
            session_count += Self::insert_row(&conn, "session_v2", row, &["session_v2"]);
            if let Some(messages) = item.get("messages").and_then(|v| v.as_array()) {
                for message in messages {
                    message_count += Self::insert_row(&conn, "session_message", message, &["session_message"]);
                }
            }
            if let Some(parts) = item.get("parts").and_then(|v| v.as_array()) {
                for part in parts {
                    part_count += Self::insert_row(&conn, "session_part", part, &["session_part"]);
                }
            }
        }
        if was_enabled == 1 {
            let _ = conn.execute("PRAGMA foreign_keys = ON", params![]);
        }
        self.status_message = self.t("import_done")
            .replacen("{}", &session_count.to_string(), 1)
            .replacen("{}", &message_count.to_string(), 1)
            .replacen("{}", &part_count.to_string(), 1);
        self.load_sessions();
    }

    fn delete_archived(&mut self) {
        let db_path = match &self.db_path {
            Some(path) => path.clone(),
            None => return,
        };
        let conn = match Connection::open(&db_path) {
            Ok(conn) => conn,
            Err(_) => return,
        };
        let ids: Vec<String> = match conn.prepare(
            "SELECT id FROM session_v2 WHERE time_archived IS NOT NULL",
        ) {
            Ok(mut stmt) => match stmt.query_map(params![], |row| row.get::<_, String>(0)) {
                Ok(rows) => rows.flatten().collect(),
                Err(_) => Vec::new(),
            },
            Err(_) => Vec::new(),
        };
        if ids.is_empty() {
            self.status_message = self.t("no_archived");
            return;
        }
        let _ = conn.execute("PRAGMA foreign_keys = ON", params![]);
        for id in &ids {
            let _ = conn.execute("DELETE FROM session_v2 WHERE id = ?", params![id.as_str()]);
        }
        self.status_message = format!("{} {}", self.t("delete"), ids.len());
        self.load_sessions();
    }

    fn format_time(timestamp: i64) -> String {
        let dt = Local.timestamp_opt(timestamp / 1000, 0);
        match dt.single() {
            Some(dt) => dt.format("%m/%d %H:%M").to_string(),
            None => "--".to_string(),
        }
    }

    fn vacuum_database(&mut self) {
        if let Some(db_path) = &self.db_path {
            if let Ok(conn) = Connection::open(db_path) {
                if conn.execute("VACUUM", params![]).is_ok() {
                    self.status_message = "压缩完成 ✓".to_string();
                }
            }
        }
    }

    fn select_all(&mut self) {
        self.selected_sessions = (0..self.sessions.len()).collect();
    }

    fn deselect_all(&mut self) {
        self.selected_sessions.clear();
    }
}

impl eframe::App for App {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // 顶部面板
        egui::TopBottomPanel::top("top_panel").show(ctx, |ui| {
            ui.add_space(4.0);
            ui.horizontal(|ui| {
                // 语言切换
                let lang_btn = egui::Button::new(
                    egui::RichText::new(self.t("lang_switch")).strong()
                ).min_size(Vec2::new(40.0, 28.0));
                if ui.add(lang_btn).clicked() {
                    self.lang = if self.lang == "zh" { "en".to_string() } else { "zh".to_string() };
                }

                ui.add_space(8.0);
                ui.separator();
                ui.add_space(8.0);

                ui.label(egui::RichText::new(self.t("sessions")).strong());

                ui.add_space(8.0);
                ui.separator();
                ui.add_space(8.0);

                // 操作按钮
                if ui.button(self.t("refresh")).clicked() {
                    self.load_sessions();
                }

                if ui.button(self.t("vacuum")).clicked() {
                    self.vacuum_database();
                }

                if ui.button(self.t("delete_archived")).clicked() {
                    self.confirm_action = Some("archived".to_string());
                }

                // 右侧状态
                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                    ui.label(
                        egui::RichText::new(&self.status_message)
                            .color(Color32::GRAY)
                            .small()
                    );
                });
            });
            ui.add_space(4.0);
        });

        // 底部面板
        egui::TopBottomPanel::bottom("bottom_panel").show(ctx, |ui| {
            ui.add_space(4.0);
            ui.horizontal(|ui| {
                if ui.button(self.t("select_all")).clicked() {
                    self.select_all();
                }
                if ui.button(self.t("deselect_all")).clicked() {
                    self.deselect_all();
                }
                
                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                    let delete_btn = egui::Button::new(
                        egui::RichText::new(self.t("delete")).color(Color32::from_rgb(200, 50, 50))
                    );
                    if ui.add(delete_btn).clicked() && !self.selected_sessions.is_empty() {
                        self.confirm_action = Some("selected".to_string());
                    }
                });
            });
            ui.add_space(4.0);
        });

        // 中央面板
        egui::CentralPanel::default().show(ctx, |ui| {
            // 筛选栏
            ui.add_space(4.0);
            ui.horizontal(|ui| {
                let filter_text = self.t("filter_placeholder");
                ui.add(egui::TextEdit::singleline(&mut self.filter_text).hint_text(filter_text));
                
                ui.add_space(8.0);
                
                let time_all = self.t("time_all");
                let time_today = self.t("time_today");
                let time_week = self.t("time_week");
                let time_month = self.t("time_month");

                let current_time_text = match self.time_filter.as_str() {
                    "all" => &time_all,
                    "today" => &time_today,
                    "week" => &time_week,
                    "month" => &time_month,
                    _ => &time_all,
                };

                egui::ComboBox::from_id_source("time_filter")
                    .selected_text(current_time_text.clone())
                    .width(100.0)
                    .show_ui(ui, |ui| {
                        ui.selectable_value(&mut self.time_filter, "all".to_string(), time_all.clone());
                        ui.selectable_value(&mut self.time_filter, "today".to_string(), time_today.clone());
                        ui.selectable_value(&mut self.time_filter, "week".to_string(), time_week.clone());
                        ui.selectable_value(&mut self.time_filter, "month".to_string(), time_month.clone());
                    });

                ui.add_space(8.0);

                let status_all = self.t("status_all");
                let status_active = self.t("status_active");
                let status_archived = self.t("status_archived");
                let current_status_text = match self.status_filter.as_str() {
                    "active" => &status_active,
                    "archived" => &status_archived,
                    _ => &status_all,
                };
                egui::ComboBox::from_id_source("status_filter")
                    .selected_text(current_status_text.clone())
                    .width(100.0)
                    .show_ui(ui, |ui| {
                        ui.selectable_value(&mut self.status_filter, "all".to_string(), status_all.clone());
                        ui.selectable_value(&mut self.status_filter, "active".to_string(), status_active.clone());
                        ui.selectable_value(&mut self.status_filter, "archived".to_string(), status_archived.clone());
                    });
            });

            ui.horizontal(|ui| {
                ui.label(self.t("archive_path"));
                ui.add(
                    egui::TextEdit::singleline(&mut self.file_path)
                        .desired_width(360.0)
                        .hint_text("opencode_sessions.json"),
                );
                if ui.button(self.t("export")).clicked() {
                    self.export_selected();
                }
                if ui.button(self.t("import")).clicked() {
                    self.confirm_action = Some("import".to_string());
                }
            });

            ui.add_space(4.0);
            ui.separator();
            ui.add_space(4.0);

            // 内容区域
            self.show_sessions(ui);
        });

        // 确认对话框（删除 / 删除已归档 / 导入）
        if self.confirm_action.is_some() {
            let action = self.confirm_action.clone().unwrap_or_default();
            let (title, message) = match action.as_str() {
                "archived" => (self.t("confirm_delete"), self.t("confirm_archived_msg")),
                "import" => (self.t("confirm_import"), self.t("confirm_import_msg")),
                _ => (self.t("confirm_delete"), self.t("confirm_delete_msg")),
            };
            egui::Window::new(title)
                .collapsible(false)
                .resizable(false)
                .anchor(egui::Align2::CENTER_CENTER, Vec2::ZERO)
                .show(ctx, |ui| {
                    ui.add_space(8.0);
                    ui.label(message);
                    ui.add_space(12.0);
                    ui.horizontal(|ui| {
                        if ui.button(self.t("yes")).clicked() {
                            match action.as_str() {
                                "archived" => self.delete_archived(),
                                "import" => self.import_archive(),
                                _ => self.delete_selected_sessions(),
                            }
                            self.confirm_action = None;
                        }
                        if ui.button(self.t("no")).clicked() {
                            self.confirm_action = None;
                        }
                    });
                });
        }
    }
}

impl App {
    fn show_sessions(&mut self, ui: &mut egui::Ui) {
        let now = Local::now().timestamp() * 1000;
        let time_threshold = match self.time_filter.as_str() {
            "today" => {
                let today = Local::now().date_naive();
                today.and_hms_opt(0, 0, 0).unwrap().and_local_timezone(Local).unwrap().timestamp() * 1000
            }
            "week" => now - 7 * 24 * 60 * 60 * 1000,
            "month" => now - 30 * 24 * 60 * 60 * 1000,
            _ => 0,
        };

        let filtered: Vec<(usize, &Session)> = self.sessions.iter()
            .enumerate()
            .filter(|(_, s)| {
                if time_threshold > 0 && s.time_updated < time_threshold {
                    return false;
                }
                match self.status_filter.as_str() {
                    "active" if s.time_archived.is_some() => return false,
                    "archived" if s.time_archived.is_none() => return false,
                    _ => {}
                }
                if !self.filter_text.is_empty() {
                    let filter = self.filter_text.to_lowercase();
                    return s.title.to_lowercase().contains(&filter)
                        || s.directory.to_lowercase().contains(&filter)
                        || s.id.to_lowercase().contains(&filter)
                        || s.project_id.to_lowercase().contains(&filter);
                }
                true
            })
            .collect();

        if filtered.is_empty() {
            ui.centered_and_justified(|ui| {
                ui.label(
                    egui::RichText::new(self.t("no_sessions"))
                        .color(Color32::GRAY)
                        .size(16.0)
                );
            });
            return;
        }

        let messages_label = self.t("messages");
        let tokens_label = self.t("tokens");
        let cost_label = self.t("cost");
        let title_label = self.t("title");
        let version_label = self.t("version");
        let created_label = self.t("created");
        let directory_label = self.t("directory");
        let details_label = self.t("details");
        let id_label = self.t("id");
        let archived_flag = self.t("archived_flag");
        let status_label = self.t("status_archived");

        let mut groups: std::collections::BTreeMap<String, Vec<(usize, &Session)>> =
            std::collections::BTreeMap::new();
        for (idx, session) in filtered {
            let key = if session.directory.is_empty() {
                session.project_id.clone()
            } else {
                session.directory.clone()
            };
            groups.entry(key).or_default().push((idx, session));
        }

        let detail_height = if self.selected_sessions.is_empty() { 0.0 } else { 130.0 };
        let max_height = (ui.available_height() - detail_height).max(80.0);
        egui::ScrollArea::vertical().max_height(max_height).show(ui, |ui| {
            for (directory, items) in groups {
                let short = short_directory(&directory);
                let latest = items.iter().map(|(_, session)| session.time_updated).max().unwrap_or(0);
                ui.collapsing(
                    format!("{} ({}) [{}]", short, items.len(), Self::format_time(latest)),
                    |ui| {
                        for (idx, session) in items {
                            let is_selected = self.selected_sessions.contains(&idx);
                            let time_str = Self::format_time(session.time_updated);
                            let title = if session.title.is_empty() { "(untitled)" } else { &session.title };
                            let flag = if session.time_archived.is_some() {
                                archived_flag.clone()
                            } else {
                                String::new()
                            };
                            let label = format!(
                                "[{}] {}{} | {} {} | {} {} | {} ${:.2}",
                                time_str,
                                title,
                                flag,
                                session.message_count,
                                messages_label,
                                session.tokens_total(),
                                tokens_label,
                                cost_label,
                                session.cost,
                            );
                            if ui.selectable_label(is_selected, label).clicked() {
                                if is_selected {
                                    self.selected_sessions.retain(|&x| x != idx);
                                } else {
                                    self.selected_sessions.push(idx);
                                }
                            }
                        }
                    },
                );
            }
        });

        if let Some(&idx) = self.selected_sessions.first() {
            if let Some(session) = self.sessions.get(idx) {
                ui.add_space(6.0);
                ui.separator();
                ui.label(egui::RichText::new(&details_label).strong());
                ui.label(format!("{}: {}", id_label, session.id));
                ui.label(format!("{}: {}", title_label, session.title));
                ui.label(format!("{}: {}", version_label, session.version));
                ui.label(format!("{}: {}", created_label, Self::format_time(session.time_created)));
                ui.label(format!("{}: {}", directory_label, session.directory));
                let archived_mark = if session.time_archived.is_some() {
                    format!(" | {}: ✓", status_label)
                } else {
                    String::new()
                };
                ui.label(format!(
                    "{}: {} | {}: {} | {} ${:.2}{}",
                    messages_label,
                    session.message_count,
                    tokens_label,
                    session.tokens_total(),
                    cost_label,
                    session.cost,
                    archived_mark,
                ));
            }
        }
    }

}

fn short_directory(path: &str) -> String {
    let normalized = path.replace('\\', "/");
    let trimmed = normalized.trim_end_matches('/');
    let name = trimmed.rsplit('/').next().unwrap_or(trimmed);
    if name.is_empty() {
        "(unknown)".to_string()
    } else {
        name.to_string()
    }
}

fn find_opencode_db() -> Option<PathBuf> {
    if let Ok(override_path) = std::env::var("OPENCODE_SESSION_MANAGER_DB") {
        let path = PathBuf::from(override_path);
        if path.exists() {
            return Some(path);
        }
    }
    let home = dirs::home_dir()?;
    let db_path = home.join(".local").join("share").join("opencode").join("opencode.db");
    if db_path.exists() {
        Some(db_path)
    } else {
        None
    }
}
