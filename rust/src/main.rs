use eframe::egui;
use rusqlite::{Connection, params};
use std::path::PathBuf;
use chrono::{Local, TimeZone};

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
            setup_fonts(&cc.egui_ctx);
            Ok(Box::new(App::new(cc)))
        }),
    )
}

fn setup_fonts(ctx: &egui::Context) {
    let mut fonts = egui::FontDefinitions::default();
    fonts.families
        .get_mut(&egui::FontFamily::Proportional)
        .unwrap()
        .push("fonts/NotoSansSC-Regular.ttf".to_owned());
    ctx.set_fonts(fonts);
}

#[derive(Clone, Debug)]
struct Session {
    id: String,
    title: String,
    directory: String,
    time_created: i64,
    time_updated: i64,
    time_archived: Option<i64>,
    cost: f64,
    tokens_input: i64,
    tokens_output: i64,
}

#[derive(Clone, Debug)]
struct ArchiveRecord {
    key: String,
    value: String,
}

#[derive(PartialEq, Clone)]
enum Tab {
    Sessions,
    Archive,
}

struct App {
    lang: String,
    current_tab: Tab,
    db_path: Option<PathBuf>,
    archive_db_path: Option<PathBuf>,
    sessions: Vec<Session>,
    archive_records: Vec<ArchiveRecord>,
    selected_sessions: Vec<usize>,
    selected_archive: Vec<usize>,
    filter_text: String,
    time_filter: String,
    status_message: String,
    show_delete_confirm: bool,
    delete_target: String,
}

impl App {
    fn new(_cc: &eframe::CreationContext<'_>) -> Self {
        let db_path = find_opencode_db();
        let archive_db_path = find_archive_db();

        let mut app = Self {
            lang: "zh".to_string(),
            current_tab: Tab::Sessions,
            db_path,
            archive_db_path,
            sessions: Vec::new(),
            archive_records: Vec::new(),
            selected_sessions: Vec::new(),
            selected_archive: Vec::new(),
            filter_text: String::new(),
            time_filter: "all".to_string(),
            status_message: "就绪".to_string(),
            show_delete_confirm: false,
            delete_target: String::new(),
        };

        app.load_sessions();
        app.load_archive();
        app
    }

    fn t(&self, key: &str) -> String {
        match self.lang.as_str() {
            "zh" => match key {
                "window_title" => "OpenCode 会话管理器".to_string(),
                "sessions" => "会话".to_string(),
                "archive" => "归档管理".to_string(),
                "refresh" => "刷新".to_string(),
                "select_db" => "选择数据库".to_string(),
                "vacuum" => "压缩".to_string(),
                "export" => "导出".to_string(),
                "import" => "导入".to_string(),
                "delete" => "删除".to_string(),
                "select_all" => "全选".to_string(),
                "deselect_all" => "取消全选".to_string(),
                "lang_switch" => "EN".to_string(),
                "filter_placeholder" => "筛选...".to_string(),
                "time_all" => "全部".to_string(),
                "time_today" => "今天".to_string(),
                "time_week" => "7天".to_string(),
                "time_month" => "30天".to_string(),
                "confirm_delete" => "确认删除".to_string(),
                "confirm_delete_msg" => "确定要删除选中的记录吗？\n此操作不可撤销！".to_string(),
                "yes" => "是".to_string(),
                "no" => "否".to_string(),
                "no_sessions" => "没有找到会话".to_string(),
                "no_archive" => "没有找到归档记录".to_string(),
                "total" => "总计".to_string(),
                "active" => "活跃".to_string(),
                "archived" => "已归档".to_string(),
                _ => key.to_string(),
            },
            _ => match key {
                "window_title" => "OpenCode Session Manager".to_string(),
                "sessions" => "Sessions".to_string(),
                "archive" => "Archive".to_string(),
                "refresh" => "Refresh".to_string(),
                "select_db" => "Select DB".to_string(),
                "vacuum" => "Vacuum".to_string(),
                "export" => "Export".to_string(),
                "import" => "Import".to_string(),
                "delete" => "Delete".to_string(),
                "select_all" => "Select All".to_string(),
                "deselect_all" => "Deselect All".to_string(),
                "lang_switch" => "中文".to_string(),
                "filter_placeholder" => "Filter...".to_string(),
                "time_all" => "All".to_string(),
                "time_today" => "Today".to_string(),
                "time_week" => "7 Days".to_string(),
                "time_month" => "30 Days".to_string(),
                "confirm_delete" => "Confirm Delete".to_string(),
                "confirm_delete_msg" => "Delete selected records?\nThis cannot be undone!".to_string(),
                "yes" => "Yes".to_string(),
                "no" => "No".to_string(),
                "no_sessions" => "No sessions found".to_string(),
                "no_archive" => "No archive records found".to_string(),
                "total" => "Total".to_string(),
                "active" => "Active".to_string(),
                "archived" => "Archived".to_string(),
                _ => key.to_string(),
            },
        }
    }

    fn find_opencode_db(&self) -> Option<PathBuf> {
        let home = dirs::home_dir()?;
        let db_path = home.join(".local").join("share").join("opencode").join("opencode.db");
        if db_path.exists() {
            Some(db_path)
        } else {
            None
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

        let mut stmt = match conn.prepare(
            "SELECT id, title, directory, time_created, time_updated, time_archived, 
             cost, tokens_input, tokens_output 
             FROM session ORDER BY time_updated DESC"
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
                title: row.get(1)?,
                directory: row.get(2)?,
                time_created: row.get(3)?,
                time_updated: row.get(4)?,
                time_archived: row.get(5)?,
                cost: row.get(6)?,
                tokens_input: row.get(7)?,
                tokens_output: row.get(8)?,
            })
        });

        if let Ok(rows) = rows {
            for row in rows.flatten() {
                self.sessions.push(row);
            }
        }

        self.status_message = format!("{}: {} 条记录", self.t("total"), self.sessions.len());
    }

    fn load_archive(&mut self) {
        self.archive_records.clear();

        let db_path = match &self.archive_db_path {
            Some(p) => p.clone(),
            None => return,
        };

        let conn = match Connection::open(&db_path) {
            Ok(c) => c,
            Err(e) => {
                self.status_message = format!("归档数据库打开失败: {}", e);
                return;
            }
        };

        let mut stmt = match conn.prepare("SELECT key, value FROM document ORDER BY key") {
            Ok(s) => s,
            Err(e) => {
                self.status_message = format!("查询失败: {}", e);
                return;
            }
        };

        let rows = stmt.query_map([], |row| {
            Ok(ArchiveRecord {
                key: row.get(0)?,
                value: row.get(1)?,
            })
        });

        if let Ok(rows) = rows {
            for row in rows.flatten() {
                self.archive_records.push(row);
            }
        }
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
            Err(e) => {
                self.status_message = format!("数据库打开失败: {}", e);
                return;
            }
        };

        let selected_ids: Vec<String> = self.selected_sessions.iter()
            .filter_map(|&i| self.sessions.get(i).map(|s| s.id.clone()))
            .collect();

        for id in &selected_ids {
            let _ = conn.execute("DELETE FROM session WHERE id = ?", params![id]);
        }

        self.selected_sessions.clear();
        self.load_sessions();
    }

    fn delete_selected_archive(&mut self) {
        if self.selected_archive.is_empty() {
            return;
        }

        let db_path = match &self.archive_db_path {
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

        let selected_keys: Vec<String> = self.selected_archive.iter()
            .filter_map(|&i| self.archive_records.get(i).map(|r| r.key.clone()))
            .collect();

        for key in &selected_keys {
            let _ = conn.execute("DELETE FROM document WHERE key = ?", params![key]);
        }

        self.selected_archive.clear();
        self.load_archive();
    }

    fn format_time(timestamp: i64) -> String {
        let dt = Local.timestamp_opt(timestamp / 1000, 0);
        match dt.single() {
            Some(dt) => dt.format("%m/%d %H:%M").to_string(),
            None => "--".to_string(),
        }
    }

    fn extract_preview(value: &str) -> String {
        if let Ok(data) = serde_json::from_str::<serde_json::Value>(value) {
            if let Some(prompt) = data.get("prompt").and_then(|p| p.as_array()) {
                for part in prompt {
                    if let Some(content) = part.get("content").and_then(|c| c.as_str()) {
                        if !content.is_empty() {
                            let preview = if content.len() > 50 {
                                format!("{}...", &content[..50])
                            } else {
                                content.to_string()
                            };
                            return preview;
                        }
                    }
                }
            }
        }
        "(空)".to_string()
    }
}

impl eframe::App for App {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        egui::TopBottomPanel::top("top_panel").show(ctx, |ui| {
            ui.horizontal(|ui| {
                // Language switch
                if ui.button(self.t("lang_switch")).clicked() {
                    self.lang = if self.lang == "zh" { "en".to_string() } else { "zh".to_string() };
                }

                ui.separator();

                // Tabs
                if ui.selectable_label(self.current_tab == Tab::Sessions, self.t("sessions")).clicked() {
                    self.current_tab = Tab::Sessions;
                }
                if ui.selectable_label(self.current_tab == Tab::Archive, self.t("archive")).clicked() {
                    self.current_tab = Tab::Archive;
                }

                ui.separator();

                // Action buttons
                if ui.button(self.t("refresh")).clicked() {
                    self.load_sessions();
                    self.load_archive();
                }

                if ui.button(self.t("select_db")).clicked() {
                    if let Some(path) = rfd::FileDialog::new()
                        .add_filter("SQLite", &["sqlite"])
                        .pick_file() 
                    {
                        self.db_path = Some(path);
                        self.load_sessions();
                    }
                }

                if ui.button(self.t("vacuum")).clicked() {
                    self.vacuum_database();
                }

                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                    ui.label(&self.status_message);
                });
            });
        });

        egui::TopBottomPanel::bottom("bottom_panel").show(ctx, |ui| {
            ui.horizontal(|ui| {
                if ui.button(self.t("select_all")).clicked() {
                    self.select_all();
                }
                if ui.button(self.t("deselect_all")).clicked() {
                    self.deselect_all();
                }
                if ui.button(self.t("delete")).clicked() {
                    self.show_delete_confirm = true;
                }
            });
        });

        egui::CentralPanel::default().show(ctx, |ui| {
            // Pre-compute translated strings
            let time_all = self.t("time_all");
            let time_today = self.t("time_today");
            let time_week = self.t("time_week");
            let time_month = self.t("time_month");

            // Filter row
            ui.horizontal(|ui| {
                ui.text_edit_singleline(&mut self.filter_text);
                
                let current_time_text = match self.time_filter.as_str() {
                    "all" => &time_all,
                    "today" => &time_today,
                    "week" => &time_week,
                    "month" => &time_month,
                    _ => &time_all,
                };

                egui::ComboBox::from_id_source("time_filter")
                    .selected_text(current_time_text)
                    .show_ui(ui, |ui| {
                        ui.selectable_value(&mut self.time_filter, "all".to_string(), &time_all);
                        ui.selectable_value(&mut self.time_filter, "today".to_string(), &time_today);
                        ui.selectable_value(&mut self.time_filter, "week".to_string(), &time_week);
                        ui.selectable_value(&mut self.time_filter, "month".to_string(), &time_month);
                    });
            });

            ui.separator();

            match self.current_tab {
                Tab::Sessions => self.show_sessions(ui),
                Tab::Archive => self.show_archive(ui),
            }
        });

        // Delete confirmation dialog
        if self.show_delete_confirm {
            egui::Window::new(self.t("confirm_delete"))
                .collapsible(false)
                .resizable(false)
                .show(ctx, |ui| {
                    ui.label(self.t("confirm_delete_msg"));
                    ui.horizontal(|ui| {
                        if ui.button(self.t("yes")).clicked() {
                            match self.current_tab {
                                Tab::Sessions => self.delete_selected_sessions(),
                                Tab::Archive => self.delete_selected_archive(),
                            }
                            self.show_delete_confirm = false;
                        }
                        if ui.button(self.t("no")).clicked() {
                            self.show_delete_confirm = false;
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
                and_time_from_date(today)
            }
            "week" => now - 7 * 24 * 60 * 60 * 1000,
            "month" => now - 30 * 24 * 60 * 60 * 1000,
            _ => 0,
        };

        let filtered: Vec<(usize, &Session)> = self.sessions.iter()
            .enumerate()
            .filter(|(_, s)| {
                // Time filter
                if time_threshold > 0 && s.time_updated < time_threshold {
                    return false;
                }
                // Text filter
                if !self.filter_text.is_empty() {
                    let filter = self.filter_text.to_lowercase();
                    return s.title.to_lowercase().contains(&filter) 
                        || s.directory.to_lowercase().contains(&filter);
                }
                true
            })
            .collect();

        if filtered.is_empty() {
            ui.centered_and_justified(|ui| {
                ui.label(self.t("no_sessions"));
            });
            return;
        }

        egui::ScrollArea::vertical().show(ui, |ui| {
            for (idx, session) in filtered {
                let is_selected = self.selected_sessions.contains(&idx);
                let time_str = Self::format_time(session.time_updated);
                let title = if session.title.is_empty() { "(untitled)" } else { &session.title };
                let label = format!("[{}] {} - {}", time_str, title, session.directory);

                if ui.selectable_label(is_selected, &label).clicked() {
                    if is_selected {
                        self.selected_sessions.retain(|&x| x != idx);
                    } else {
                        self.selected_sessions.push(idx);
                    }
                }
            }
        });
    }

    fn show_archive(&mut self, ui: &mut egui::Ui) {
        let filtered: Vec<(usize, &ArchiveRecord)> = self.archive_records.iter()
            .enumerate()
            .filter(|(_, r)| {
                if !self.filter_text.is_empty() {
                    let filter = self.filter_text.to_lowercase();
                    return r.key.to_lowercase().contains(&filter);
                }
                true
            })
            .collect();

        if filtered.is_empty() {
            ui.centered_and_justified(|ui| {
                ui.label(self.t("no_archive"));
            });
            return;
        }

        egui::ScrollArea::vertical().show(ui, |ui| {
            for (idx, record) in filtered {
                let is_selected = self.selected_archive.contains(&idx);
                let preview = Self::extract_preview(&record.value);
                let label = format!("{}: {}", record.key, preview);

                if ui.selectable_label(is_selected, &label).clicked() {
                    if is_selected {
                        self.selected_archive.retain(|&x| x != idx);
                    } else {
                        self.selected_archive.push(idx);
                    }
                }
            }
        });
    }

    fn select_all(&mut self) {
        match self.current_tab {
            Tab::Sessions => {
                self.selected_sessions = (0..self.sessions.len()).collect();
            }
            Tab::Archive => {
                self.selected_archive = (0..self.archive_records.len()).collect();
            }
        }
    }

    fn deselect_all(&mut self) {
        match self.current_tab {
            Tab::Sessions => self.selected_sessions.clear(),
            Tab::Archive => self.selected_archive.clear(),
        }
    }

    fn vacuum_database(&mut self) {
        let db_path = match &self.db_path {
            Some(p) => p.clone(),
            None => return,
        };

        if let Ok(conn) = Connection::open(&db_path) {
            if conn.execute("VACUUM", params![]).is_ok() {
                self.status_message = "压缩完成".to_string();
            }
        }
    }
}

fn find_opencode_db() -> Option<PathBuf> {
    let home = dirs::home_dir()?;
    let db_path = home.join(".local").join("share").join("opencode").join("opencode.db");
    if db_path.exists() {
        Some(db_path)
    } else {
        None
    }
}

fn find_archive_db() -> Option<PathBuf> {
    let app_data = dirs::config_dir().or_else(dirs::data_dir)?;
    let db_path = app_data.join("ai.opencode.desktop").join("drafts.sqlite");
    if db_path.exists() {
        Some(db_path)
    } else {
        None
    }
}

fn and_time_from_date(date: chrono::NaiveDate) -> i64 {
    let datetime = date.and_hms_opt(0, 0, 0).unwrap();
    datetime.and_local_timezone(Local).unwrap().timestamp() * 1000
}
