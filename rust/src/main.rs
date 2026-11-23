use eframe::egui::{self, FontData, FontDefinitions, FontFamily, Color32, Style, Rounding, Vec2};
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
    version: String,
    time_created: i64,
    time_updated: i64,
    time_archived: Option<i64>,
    cost: f64,
    tokens_input: i64,
    tokens_output: i64,
}

struct App {
    lang: String,
    db_path: Option<PathBuf>,
    sessions: Vec<Session>,
    selected_sessions: Vec<usize>,
    filter_text: String,
    time_filter: String,
    status_message: String,
    show_delete_confirm: bool,
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
            status_message: "就绪".to_string(),
            show_delete_confirm: false,
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
                "select_all" => "全选".to_string(),
                "deselect_all" => "取消全选".to_string(),
                "lang_switch" => "EN".to_string(),
                "filter_placeholder" => "🔍 筛选...".to_string(),
                "time_all" => "全部时间".to_string(),
                "time_today" => "今天".to_string(),
                "time_week" => "最近7天".to_string(),
                "time_month" => "最近30天".to_string(),
                "confirm_delete" => "确认删除".to_string(),
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
                "select_all" => "Select All".to_string(),
                "deselect_all" => "Deselect All".to_string(),
                "lang_switch" => "中文".to_string(),
                "filter_placeholder" => "🔍 Filter...".to_string(),
                "time_all" => "All Time".to_string(),
                "time_today" => "Today".to_string(),
                "time_week" => "7 Days".to_string(),
                "time_month" => "30 Days".to_string(),
                "confirm_delete" => "Confirm Delete".to_string(),
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
            "SELECT id, title, directory, version, time_created, time_updated, \
             time_archived, cost, tokens_input, tokens_output \
             FROM session_v2 ORDER BY time_updated DESC",
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
                version: row.get(3).unwrap_or_default(),
                time_created: row.get(4)?,
                time_updated: row.get(5)?,
                time_archived: row.get(6)?,
                cost: row.get(7).unwrap_or(0.0),
                tokens_input: row.get(8).unwrap_or(0),
                tokens_output: row.get(9).unwrap_or(0),
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
                        self.show_delete_confirm = true;
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
                    .selected_text(current_time_text)
                    .width(100.0)
                    .show_ui(ui, |ui| {
                        ui.selectable_value(&mut self.time_filter, "all".to_string(), &time_all);
                        ui.selectable_value(&mut self.time_filter, "today".to_string(), &time_today);
                        ui.selectable_value(&mut self.time_filter, "week".to_string(), &time_week);
                        ui.selectable_value(&mut self.time_filter, "month".to_string(), &time_month);
                    });
            });
            ui.add_space(4.0);
            ui.separator();
            ui.add_space(4.0);

            // 内容区域
            self.show_sessions(ui);
        });

        // 删除确认对话框
        if self.show_delete_confirm {
            egui::Window::new(self.t("confirm_delete"))
                .collapsible(false)
                .resizable(false)
                .anchor(egui::Align2::CENTER_CENTER, Vec2::ZERO)
                .show(ctx, |ui| {
                    ui.add_space(8.0);
                    ui.label(self.t("confirm_delete_msg"));
                    ui.add_space(12.0);
                    ui.horizontal(|ui| {
                        if ui.button(self.t("yes")).clicked() {
                            self.delete_selected_sessions();
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
                ui.label(
                    egui::RichText::new(self.t("no_sessions"))
                        .color(Color32::GRAY)
                        .size(16.0)
                );
            });
            return;
        }

        egui::ScrollArea::vertical().show(ui, |ui| {
            for (idx, session) in filtered {
                let is_selected = self.selected_sessions.contains(&idx);
                let time_str = Self::format_time(session.time_updated);
                let title = if session.title.is_empty() { "(untitled)" } else { &session.title };
                
                let bg_color = if is_selected {
                    Color32::from_rgb(0, 120, 215)
                } else if idx % 2 == 0 {
                    Color32::from_rgb(245, 245, 245)
                } else {
                    Color32::WHITE
                };

                let response = ui.allocate_response(Vec2::new(ui.available_width(), 36.0), egui::Sense::click());
                
                // 绘制背景
                if response.hovered() || is_selected {
                    let rect = response.rect;
                    ui.painter().rect_filled(rect, Rounding::same(4.0), bg_color);
                }

                // 绘制内容
                let rect = response.rect;
                let text_color = if is_selected { Color32::WHITE } else { Color32::BLACK };
                
                ui.painter().text(
                    rect.left_center() + Vec2::new(12.0, 0.0),
                    egui::Align2::LEFT_CENTER,
                    format!("[{}] {}", time_str, title),
                    egui::FontId::proportional(14.0),
                    text_color,
                );

                // 目录（右侧）
                let dir_display = if session.directory.len() > 30 {
                    format!("...{}", &session.directory[session.directory.len()-27..])
                } else {
                    session.directory.clone()
                };
                ui.painter().text(
                    rect.right_center() + Vec2::new(-12.0, 0.0),
                    egui::Align2::RIGHT_CENTER,
                    dir_display,
                    egui::FontId::proportional(12.0),
                    if is_selected { Color32::WHITE } else { Color32::GRAY },
                );

                if response.clicked() {
                    if is_selected {
                        self.selected_sessions.retain(|&x| x != idx);
                    } else {
                        self.selected_sessions.push(idx);
                    }
                }
            }
        });
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
