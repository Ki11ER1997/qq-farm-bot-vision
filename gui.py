import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import threading
import logging
import keyboard
from utils.farm_bot_cv import FarmBotCV

class FarmBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("QQ经典农场助手 - V1.0")
        self.root.geometry("750x550")
        self.root.minsize(650, 450)
        self.root.resizable(False, False)
        
        # 窗口居中显示
        self.center_window()
        
        # 设置窗口图标
        try:
            import os
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assert', 'icon.ico')
            self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"设置图标失败: {str(e)}")
        
        # 配置自定义主题
        self.setup_custom_theme()
        
        # 加载配置
        import os
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
        self.config = configparser.ConfigParser(inline_comment_prefixes=('#',))
        self.config.read(self.config_path, encoding="utf-8")
        
        # 初始化机器人
        self.bot = None
        self.bot_thread = None
        self.running = False
        self.status_timer_id = None
        
        # 创建界面
        self.create_widgets()
        
        # 配置日志
        self.setup_logging()
        
        # 绑定全局快捷键
        self.bind_global_shortcuts()
        
        # 启动状态检查定时器
        self.check_status_timer()
    
    def create_widgets(self):
        # 创建主框架
        main_frame = tk.Frame(self.root, bg=self.colors['background'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 顶部状态栏
        status_frame = ttk.LabelFrame(main_frame, text="机器人状态", padding="5", style='Custom.TLabelframe')
        status_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=2)
        
        self.status_var = tk.StringVar(value="未启动")
        status_label = tk.Label(status_frame, textvariable=self.status_var, font=self.fonts['status'], 
                                bg=self.colors['surface'], fg=self.colors['text_secondary'])
        status_label.pack(anchor=tk.W)
        
        # 左侧控制区域
        control_frame = ttk.LabelFrame(main_frame, text="控制", padding="5", style='Custom.TLabelframe')
        control_frame.grid(row=1, column=0, sticky="nsew", pady=2, padx=(0, 2), rowspan=2)
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_rowconfigure(4, weight=1)
        
        button_frame = tk.Frame(control_frame, bg=self.colors['surface'])
        button_frame.pack(fill=tk.X, pady=2)
        
        self.start_button = ttk.Button(button_frame, text="启动", command=self.start_bot, style='Primary.TButton', width=15)
        self.start_button.pack(fill=tk.X, pady=1)
        
        self.pause_button = ttk.Button(button_frame, text="暂停", command=self.pause_bot, state=tk.DISABLED, style='Secondary.TButton', width=15)
        self.pause_button.pack(fill=tk.X, pady=1)
        
        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_bot, state=tk.DISABLED, style='Danger.TButton', width=15)
        self.stop_button.pack(fill=tk.X, pady=1)
        
        # 配置区域
        config_frame = ttk.LabelFrame(control_frame, text="配置", padding="5", style='Custom.TLabelframe')
        config_frame.pack(fill=tk.X, pady=2)
        
        # 检查间隔
        interval_frame = tk.Frame(config_frame, bg=self.colors['surface'])
        interval_frame.pack(fill=tk.X, pady=1)
        
        tk.Label(interval_frame, text="检查间隔:", width=8, bg=self.colors['surface'], fg=self.colors['text'], font=self.fonts['body']).pack(side=tk.LEFT, padx=2)
        self.interval_var = tk.StringVar(value=self.config.get('bot', 'check_interval'))
        ttk.Entry(interval_frame, textvariable=self.interval_var, style='Custom.TEntry', width=8).pack(side=tk.LEFT, padx=2)
        tk.Label(interval_frame, text="秒", bg=self.colors['surface'], fg=self.colors['text_secondary'], font=self.fonts['body']).pack(side=tk.LEFT, padx=2)
        
        # 好友冷却时间
        cooldown_frame = tk.Frame(config_frame, bg=self.colors['surface'])
        cooldown_frame.pack(fill=tk.X, pady=1)
        
        tk.Label(cooldown_frame, text="好友冷却:", width=8, bg=self.colors['surface'], fg=self.colors['text'], font=self.fonts['body']).pack(side=tk.LEFT, padx=2)
        self.friend_colddown_var = tk.StringVar(value=self.config.get('bot', 'friend_colddown_time'))
        ttk.Entry(cooldown_frame, textvariable=self.friend_colddown_var, style='Custom.TEntry', width=8).pack(side=tk.LEFT, padx=2)
        tk.Label(cooldown_frame, text="秒", bg=self.colors['surface'], fg=self.colors['text_secondary'], font=self.fonts['body']).pack(side=tk.LEFT, padx=2)
        
        # 调试模式
        debug_frame = tk.Frame(config_frame, bg=self.colors['surface'])
        debug_frame.pack(fill=tk.X, pady=1)
        
        self.debug_var = tk.BooleanVar(value=self.config.getboolean('bot', 'debug_mode'))
        ttk.Checkbutton(debug_frame, text="调试模式", variable=self.debug_var, style='Custom.TCheckbutton').pack(anchor=tk.W, padx=2)
        
        # 保存配置按钮
        ttk.Button(config_frame, text="保存配置", command=self.save_config, style='Default.TButton').pack(fill=tk.X, pady=2)
        
        # 创建菜单框架
        menu_frame = tk.Frame(control_frame, bg=self.colors['surface'])
        menu_frame.pack(fill=tk.X, pady=2)
        
        # 创建功能菜单按钮
        self.menu_var = tk.StringVar(value="功能")
        menu_button = ttk.Menubutton(menu_frame, text="功能", direction="below", style='Custom.TMenubutton')
        menu_button.pack(side=tk.LEFT, padx=2)
        
        # 创建下拉菜单 - 深色主题适配
        menu = tk.Menu(menu_button, tearoff=0, bg=self.colors['surface_dark'], fg=self.colors['text'], 
                      activebackground=self.colors['primary'], activeforeground='white', 
                      font=self.fonts['body'], borderwidth=0, relief='flat')
        menu_button.config(menu=menu)
        
        # 创建内容显示区域
        self.content_frame = tk.Frame(control_frame, bg=self.colors['surface'])
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 自家农场功能框架
        self.self_farm_frame = tk.Frame(self.content_frame, bg=self.colors['surface'])
        
        # 自家农场功能
        self.enable_self_var = tk.BooleanVar(value=self.config.getboolean('bot', 'enable_process_self'))
        ttk.Checkbutton(self.self_farm_frame, text="处理自家农场", variable=self.enable_self_var, style='Custom.TCheckbutton').pack(anchor=tk.W, pady=2, padx=5)
        
        self.enable_harvest_var = tk.BooleanVar(value=self.config.getboolean('self', 'enable_harvest'))
        ttk.Checkbutton(self.self_farm_frame, text="收获作物", variable=self.enable_harvest_var, style='Custom.TCheckbutton').pack(anchor=tk.W, pady=1, padx=15)
        
        self.enable_watering_var = tk.BooleanVar(value=self.config.getboolean('self', 'enable_watering'))
        ttk.Checkbutton(self.self_farm_frame, text="浇水", variable=self.enable_watering_var, style='Custom.TCheckbutton').pack(anchor=tk.W, pady=1, padx=15)
        
        self.enable_remove_grass_var = tk.BooleanVar(value=self.config.getboolean('self', 'enable_remove_grass'))
        ttk.Checkbutton(self.self_farm_frame, text="除草", variable=self.enable_remove_grass_var, style='Custom.TCheckbutton').pack(anchor=tk.W, pady=1, padx=15)
        
        self.enable_remove_bug_var = tk.BooleanVar(value=self.config.getboolean('self', 'enable_remove_bug'))
        ttk.Checkbutton(self.self_farm_frame, text="除虫", variable=self.enable_remove_bug_var, style='Custom.TCheckbutton').pack(anchor=tk.W, pady=1, padx=15)
        
        self.enable_daily_free_var = tk.BooleanVar(value=self.config.getboolean('self', 'enable_daily_free'))
        ttk.Checkbutton(self.self_farm_frame, text="领取每日礼包", variable=self.enable_daily_free_var, style='Custom.TCheckbutton').pack(anchor=tk.W, pady=1, padx=15)
        
        # 好友农场功能框架
        self.friend_farm_frame = tk.Frame(self.content_frame, bg=self.colors['surface'])
        
        # 好友农场功能
        self.enable_friend_var = tk.BooleanVar(value=self.config.getboolean('bot', 'enable_process_friend'))
        ttk.Checkbutton(self.friend_farm_frame, text="处理好友农场", variable=self.enable_friend_var, style='Custom.TCheckbutton').pack(anchor=tk.W, pady=2, padx=5)
        
        self.enable_steal_var = tk.BooleanVar(value=self.config.getboolean('friend', 'enable_steal'))
        ttk.Checkbutton(self.friend_farm_frame, text="偷取作物", variable=self.enable_steal_var, style='Custom.TCheckbutton').pack(anchor=tk.W, pady=1, padx=15)
        
        self.enable_help_watering_var = tk.BooleanVar(value=self.config.getboolean('friend', 'enable_help_watering'))
        ttk.Checkbutton(self.friend_farm_frame, text="帮忙浇水", variable=self.enable_help_watering_var, style='Custom.TCheckbutton').pack(anchor=tk.W, pady=1, padx=15)
        
        self.enable_help_remove_grass_var = tk.BooleanVar(value=self.config.getboolean('friend', 'enable_help_remove_grass'))
        ttk.Checkbutton(self.friend_farm_frame, text="帮忙除草", variable=self.enable_help_remove_grass_var, style='Custom.TCheckbutton').pack(anchor=tk.W, pady=1, padx=15)
        
        self.enable_help_remove_bugs_var = tk.BooleanVar(value=self.config.getboolean('friend', 'enable_help_remove_bugs'))
        ttk.Checkbutton(self.friend_farm_frame, text="帮忙除虫", variable=self.enable_help_remove_bugs_var, style='Custom.TCheckbutton').pack(anchor=tk.W, pady=1, padx=15)
        
        # 阈值调整功能框架
        self.threshold_frame = tk.Frame(self.content_frame, bg=self.colors['surface'])
        
        # 阈值调整区域 - 更紧凑的布局
        threshold_canvas = tk.Canvas(self.threshold_frame, bg=self.colors['surface'], highlightthickness=0)
        threshold_scrollbar = ttk.Scrollbar(self.threshold_frame, orient="vertical", command=threshold_canvas.yview, style='Custom.Vertical.TScrollbar')
        threshold_inner_frame = tk.Frame(threshold_canvas, bg=self.colors['surface'])
        
        threshold_inner_frame.bind(
            "<Configure>",
            lambda e: threshold_canvas.configure(
                scrollregion=threshold_canvas.bbox("all")
            )
        )
        
        threshold_canvas.create_window((0, 0), window=threshold_inner_frame, anchor="nw")
        threshold_canvas.configure(yscrollcommand=threshold_scrollbar.set)
        
        threshold_canvas.pack(side="left", fill="both", expand=True)
        threshold_scrollbar.pack(side="right", fill="y")
        
        # 加载阈值配置
        self.threshold_vars = {}
        threshold_section = self.config['threshold']
        
        # 阈值中文映射
        threshold_names = {
            'help_remove_bugs_frame': '帮忙除虫阈值',
            'help_remove_grass_frame': '帮忙除草阈值',
            'help_watering_frame': '帮忙浇水阈值',
            'can_steal_frame': '可偷取阈值',
            'close_x_frame': '关闭按钮阈值',
            'go_home_frame': '回家按钮阈值',
            'steal_all_frame': '一键偷取阈值',
            'watering_all_frame': '一键浇水阈值',
            'remove_all_grass_frame': '一键除草阈值',
            'remove_all_bugs_frame': '一键除虫阈值',
            'harvest_all_frame': '一键收获阈值',
            'harvest_one_frame': '单个收获阈值',
            'friend_icon_frame': '好友图标阈值',
            'welcome_back_frame': '欢迎回来阈值',
            'get_new_seed_frame': '获得新种子阈值',
            'level_up_frame': '升级提示阈值',
            'reconnect_frame': '重新登录阈值',
            'can_steal_small_frame': '好友可偷阈值',
            'can_watering_small_frame': '好友可浇水阈值',
            'can_remove_grass_small_frame': '好友可除草阈值',
            'can_remove_bugs_small_frame': '好友可除虫阈值',
            'close_x_small_frame': '好友关闭按钮阈值',
            'shop_red_frame': '商店红点阈值',
            'daily_free_frame': '每日免费礼包阈值',
            'return_farm_frame': '返回农场阈值'
        }
        
        row = 0
        col = 0
        for key, value in threshold_section.items():
            # 使用中文名称
            chinese_name = threshold_names.get(key, key.replace('_', ' '))
            
            item_frame = tk.Frame(threshold_inner_frame, bg=self.colors['surface'])
            item_frame.grid(row=row, column=col, sticky="w", padx=3, pady=1)
            
            tk.Label(item_frame, text=chinese_name, bg=self.colors['surface'], 
                    fg=self.colors['text'], font=self.fonts['body'], anchor='w').pack(side=tk.LEFT)
            
            var = tk.DoubleVar(value=float(value))
            self.threshold_vars[key] = var
            
            entry = ttk.Entry(item_frame, textvariable=var, style='Custom.TEntry', width=6)
            entry.pack(side=tk.LEFT, padx=3)
            
            col += 1
            if col >= 2:
                col = 0
                row += 1
        
        # 保存阈值按钮
        ttk.Button(threshold_inner_frame, text="保存阈值", command=self.save_thresholds, style='Default.TButton').grid(row=row+1, column=0, columnspan=2, pady=8, sticky="ew", padx=3)
        
        # 定义切换函数
        def show_frame(frame):
            # 隐藏所有框架
            self.self_farm_frame.pack_forget()
            self.friend_farm_frame.pack_forget()
            self.threshold_frame.pack_forget()
            # 显示选中的框架
            frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加菜单项
        menu.add_command(label="自家农场", command=lambda: show_frame(self.self_farm_frame))
        menu.add_command(label="好友农场", command=lambda: show_frame(self.friend_farm_frame))
        menu.add_separator()
        menu.add_command(label="阈值调整", command=lambda: show_frame(self.threshold_frame))
        
        # 默认显示自家农场
        show_frame(self.self_farm_frame)
        
        # 右侧日志区域
        right_frame = tk.Frame(main_frame, bg=self.colors['background'])
        right_frame.grid(row=1, column=1, sticky="nsew", pady=2, padx=(2, 0))
        
        # 设置网格权重
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # 日志区域
        log_frame = ttk.LabelFrame(right_frame, text="日志", padding="5", style='Custom.TLabelframe')
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, state=tk.DISABLED, 
                                bg=self.colors['surface_dark'], fg=self.colors['text'], 
                                font=self.fonts['body'], relief='flat', bd=0, 
                                insertbackground=self.colors['primary'])
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview, style='Custom.Vertical.TScrollbar')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 为状态标签添加颜色变化效果
        self.status_label = status_label
        self.update_status_color()
        
        # 添加按钮微交互效果
        self.add_button_hover_effects()
        
        # 绑定快捷键
        self.bind_shortcuts()
    
    def setup_logging(self):
        # 创建一个日志处理器，将日志输出到GUI
        class GUILogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
            
            def emit(self, record):
                msg = self.format(record)
                def append():
                    # 临时启用文本组件以插入日志
                    self.text_widget.config(state=tk.NORMAL)
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.see(tk.END)
                    # 重新禁用文本组件
                    self.text_widget.config(state=tk.DISABLED)
                self.text_widget.after(0, append)
        
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # 清除现有的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 添加GUI处理器
        gui_handler = GUILogHandler(self.log_text)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        gui_handler.setFormatter(formatter)
        root_logger.addHandler(gui_handler)
    
    def start_bot(self):
        # 首先禁用启动按钮，防止重复点击
        self.start_button.config(state=tk.DISABLED)
        
        # 重新绑定快捷键，确保它们能正常工作
        self.bind_shortcuts()
        
        # 重新配置日志系统，确保日志输出正常
        self.setup_logging()
        
        def start_bot_async():
            try:
                # 确保所有资源已释放
                if self.bot or self.bot_thread:
                    print("检测到未释放的资源，正在清理...")
                    if self.bot:
                        self.bot.stop()
                    if self.bot_thread and self.bot_thread.is_alive():
                        self.bot_thread.join(timeout=1.0)
                    self.bot = None
                    self.bot_thread = None
                    self.running = False
                
                # 保存配置
                def save_config_sync():
                    try:
                        # 更新配置
                        self.config.set('bot', 'check_interval', self.interval_var.get())
                        self.config.set('bot', 'friend_colddown_time', self.friend_colddown_var.get())
                        self.config.set('bot', 'debug_mode', str(self.debug_var.get()))
                        self.config.set('bot', 'enable_process_self', str(self.enable_self_var.get()))
                        self.config.set('bot', 'enable_process_friend', str(self.enable_friend_var.get()))
                        
                        self.config.set('self', 'enable_harvest', str(self.enable_harvest_var.get()))
                        self.config.set('self', 'enable_watering', str(self.enable_watering_var.get()))
                        self.config.set('self', 'enable_remove_grass', str(self.enable_remove_grass_var.get()))
                        self.config.set('self', 'enable_remove_bug', str(self.enable_remove_bug_var.get()))
                        self.config.set('self', 'enable_daily_free', str(self.enable_daily_free_var.get()))
                        
                        self.config.set('friend', 'enable_steal', str(self.enable_steal_var.get()))
                        self.config.set('friend', 'enable_help_watering', str(self.enable_help_watering_var.get()))
                        self.config.set('friend', 'enable_help_remove_grass', str(self.enable_help_remove_grass_var.get()))
                        self.config.set('friend', 'enable_help_remove_bugs', str(self.enable_help_remove_bugs_var.get()))
                        
                        # 保存配置到文件
                        with open(self.config_path, 'w', encoding='utf-8') as f:
                            self.config.write(f)
                        
                        # 使用print而不是logging，避免日志系统问题
                        print("配置保存成功")
                        return True
                    except Exception as e:
                        print(f"保存配置失败: {str(e)}")
                        return False
                
                # 保存配置
                if not save_config_sync():
                    def show_error():
                        messagebox.showerror("错误", "保存配置失败")
                        self.start_button.config(state=tk.NORMAL)
                    self.root.after(0, show_error)
                    return
                
                # 重新加载配置
                self.config.read(self.config_path, encoding="utf-8")
                
                # 创建机器人实例
                check_interval = float(self.interval_var.get())
                debug_mode = self.debug_var.get()
                
                # 使用print而不是logging，避免日志系统问题
                print("正在初始化机器人...")
                self.bot = FarmBotCV(check_interval, debug_mode, self.config)
                
                # 启动机器人线程
                self.running = True
                self.bot_thread = threading.Thread(target=self.bot.start)
                self.bot_thread.daemon = True
                self.bot_thread.start()
                
                # 更新状态和按钮
                def update_ui():
                    self.status_var.set("运行中")
                    self.update_status_color()
                    self.pause_button.config(state=tk.NORMAL)
                    self.stop_button.config(state=tk.NORMAL)
                    print("机器人启动成功")
                
                # 在主线程中更新UI
                self.root.after(0, update_ui)
            except Exception as e:
                def show_error():
                    messagebox.showerror("错误", f"启动机器人失败: {str(e)}")
                    print(f"启动机器人失败: {str(e)}")
                    self.start_button.config(state=tk.NORMAL)
                
                # 在主线程中显示错误
                self.root.after(0, show_error)
        
        # 在后台线程中启动机器人
        threading.Thread(target=start_bot_async, daemon=True).start()
    
    def pause_bot(self, event=None):
        if self.bot:
            self.bot.pause()
            if self.bot.pause_status:
                self.status_var.set("已暂停")
                self.update_status_color()
                self.pause_button.config(text="恢复")
            else:
                self.status_var.set("运行中")
                self.update_status_color()
                self.pause_button.config(text="暂停")
    
    def stop_bot(self, event=None):
        def stop_bot_async():
            if self.bot:
                # 停止机器人
                self.bot.stop()
                self.running = False
                
                # 等待机器人线程结束
                if self.bot_thread and self.bot_thread.is_alive():
                    # 设置一个较短的超时时间，避免程序卡住
                    self.bot_thread.join(timeout=1.0)
                
                # 清理资源
                self.bot_thread = None
                self.bot = None
                
                # 更新状态和按钮
                def update_ui():
                    self.status_var.set("已停止")
                    self.update_status_color()
                    self.start_button.config(state=tk.NORMAL)
                    self.pause_button.config(state=tk.DISABLED, text="暂停")
                    self.stop_button.config(state=tk.DISABLED)
                    # 使用print而不是logging，避免日志系统问题
                    print("机器人已停止")
                
                # 在主线程中更新UI
                self.root.after(0, update_ui)
        
        # 在后台线程中停止机器人
        threading.Thread(target=stop_bot_async, daemon=True).start()
    
    def save_config(self):
        try:
            # 更新配置
            self.config.set('bot', 'check_interval', self.interval_var.get())
            self.config.set('bot', 'friend_colddown_time', self.friend_colddown_var.get())
            self.config.set('bot', 'debug_mode', str(self.debug_var.get()))
            self.config.set('bot', 'enable_process_self', str(self.enable_self_var.get()))
            self.config.set('bot', 'enable_process_friend', str(self.enable_friend_var.get()))
            
            self.config.set('self', 'enable_harvest', str(self.enable_harvest_var.get()))
            self.config.set('self', 'enable_watering', str(self.enable_watering_var.get()))
            self.config.set('self', 'enable_remove_grass', str(self.enable_remove_grass_var.get()))
            self.config.set('self', 'enable_remove_bug', str(self.enable_remove_bug_var.get()))
            self.config.set('self', 'enable_daily_free', str(self.enable_daily_free_var.get()))
            
            self.config.set('friend', 'enable_steal', str(self.enable_steal_var.get()))
            self.config.set('friend', 'enable_help_watering', str(self.enable_help_watering_var.get()))
            self.config.set('friend', 'enable_help_remove_grass', str(self.enable_help_remove_grass_var.get()))
            self.config.set('friend', 'enable_help_remove_bugs', str(self.enable_help_remove_bugs_var.get()))
            
            # 保存配置到文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            logging.info("配置保存成功")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
            logging.error(f"保存配置失败: {str(e)}")
    
    def save_thresholds(self):
        try:
            # 更新阈值配置
            for key, var in self.threshold_vars.items():
                self.config.set('threshold', key, str(var.get()))
            
            # 保存配置到文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            logging.info("阈值保存成功")
            messagebox.showinfo("成功", "阈值保存成功")
        except Exception as e:
            messagebox.showerror("错误", f"保存阈值失败: {str(e)}")
            logging.error(f"保存阈值失败: {str(e)}")
    
    def bind_shortcuts(self):
        """绑定快捷键"""
        try:
            # 绑定暂停/恢复快捷键
            def on_pause(event):
                self.pause_bot()
            
            # 绑定停止快捷键
            def on_stop(event):
                self.stop_bot()
            
            # 使用bind_all确保在所有控件上都生效
            self.root.bind_all('<Control-p>', on_pause)
            self.root.bind_all('<Control-s>', on_stop)
            print("快捷键绑定成功")
        except Exception as e:
            print(f"快捷键绑定失败: {str(e)}")
    
    def bind_global_shortcuts(self):
        """绑定全局快捷键，即使程序在后台也能响应"""
        # 添加防抖机制，避免多次触发
        import time
        import threading
        last_pause_time = 0
        last_stop_time = 0
        cooldown = 1.0  # 1秒冷却时间，确保足够长以避免重复触发
        
        def on_global_pause():
            nonlocal last_pause_time
            current_time = time.time()
            if current_time - last_pause_time > cooldown:
                print("全局快捷键 Ctrl+P 被触发")
                self.pause_bot()
                last_pause_time = current_time
        
        def on_global_stop():
            nonlocal last_stop_time
            current_time = time.time()
            if current_time - last_stop_time > cooldown:
                print("全局快捷键 Ctrl+S 被触发")
                self.stop_bot()
                last_stop_time = current_time
        
        def keyboard_listener():
            """键盘监听线程，确保全局快捷键在打包后也能正常工作"""
            try:
                keyboard.wait()  # 保持监听状态
            except Exception as e:
                print(f"键盘监听异常: {str(e)}")
        
        try:
            # 绑定全局热键
            keyboard.add_hotkey('ctrl+p', on_global_pause)
            keyboard.add_hotkey('ctrl+s', on_global_stop)
            print("全局快捷键绑定成功")
            
            # 启动键盘监听线程
            self.keyboard_thread = threading.Thread(target=keyboard_listener, daemon=True)
            self.keyboard_thread.start()
            print("键盘监听线程已启动")
        except Exception as e:
            print(f"全局快捷键绑定失败: {str(e)}")
    
    def update_status_color(self):
        """根据状态更新颜色"""
        status = self.status_var.get()
        if status == "运行中":
            self.status_label.config(fg=self.colors['success'])
        elif status == "已暂停":
            self.status_label.config(fg=self.colors['warning'])
        elif status == "已停止":
            self.status_label.config(fg=self.colors['danger'])
        else:  # 未启动
            self.status_label.config(fg=self.colors['text_secondary'])
    
    def add_button_hover_effects(self):
        """为按钮添加微交互效果"""
        # 定义按钮悬停效果
        def on_enter(widget, bg_color):
            if widget.cget('state') == 'normal':
                pass  # ttk样式已处理悬停效果
        
        def on_leave(widget, bg_color):
            if widget.cget('state') == 'normal':
                pass  # ttk样式已处理离开效果
    
    def check_status_timer(self):
        """定期检查机器人的状态并更新界面"""
        try:
            if self.bot:
                # 检查机器人是否已停止
                if hasattr(self.bot, 'running') and not self.bot.running:
                    if self.running:
                        self.running = False
                        self.bot_thread = None
                        # 更新状态和按钮
                        self.status_var.set("已停止")
                        self.update_status_color()
                        self.start_button.config(state=tk.NORMAL)
                        self.pause_button.config(state=tk.DISABLED)
                        self.stop_button.config(state=tk.DISABLED)
                        logging.info("机器人已停止")
                # 检查机器人的暂停状态
                elif hasattr(self.bot, 'pause_status') and self.running:
                    if self.bot.pause_status:
                        if self.status_var.get() != "已暂停":
                            self.status_var.set("已暂停")
                            self.update_status_color()
                            self.pause_button.config(text="恢复")
                    else:
                        if self.status_var.get() != "运行中":
                            self.status_var.set("运行中")
                            self.update_status_color()
                            self.pause_button.config(text="暂停")
        except Exception as e:
            pass
        
        # 每100毫秒检查一次
        self.root.after(100, self.check_status_timer)
    
    def center_window(self):
        """将窗口居中显示在屏幕上"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_custom_theme(self):
        """配置自定义UI主题 - 深色模式"""
        # 定义深色主题色彩系统
        self.colors = {
            'primary': '#2ECC71',
            'primary_dark': '#27AE60',
            'primary_light': '#58D68D',
            'secondary': '#3498DB',
            'secondary_dark': '#2980B9',
            'danger': '#E74C3C',
            'danger_dark': '#C0392B',
            'warning': '#F39C12',
            'success': '#2ECC71',
            'text': '#ECF0F1',
            'text_secondary': '#95A5A6',
            'background': '#2B2B2B',
            'surface': '#3C3F41',
            'surface_dark': '#252526',
            'border': '#555555',
            'hover': '#4C5052'
        }
        
        # 设置窗口背景
        self.root.configure(bg=self.colors['background'])
        
        # 定义字体系统
        self.fonts = {
            'title': ('Microsoft YaHei UI', 12, 'bold'),
            'heading': ('Microsoft YaHei UI', 10, 'bold'),
            'body': ('Microsoft YaHei UI', 9),
            'small': ('Microsoft YaHei UI', 8),
            'status': ('Microsoft YaHei UI', 10, 'bold'),
            'button': ('Microsoft YaHei UI', 9, 'bold')
        }
        
        # 创建样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置全局样式
        style.configure('.', font=self.fonts['body'], background=self.colors['background'], foreground=self.colors['text'])
        
        # 配置LabelFrame样式
        style.configure('Custom.TLabelframe', background=self.colors['surface'], bordercolor=self.colors['border'], relief='solid', borderwidth=1)
        style.configure('Custom.TLabelframe.Label', font=self.fonts['heading'], background=self.colors['surface'], foreground=self.colors['primary'])
        
        # 配置Button样式
        style.configure('Primary.TButton', font=self.fonts['button'], foreground='white', background=self.colors['primary'], borderwidth=0, focuscolor='none')
        style.map('Primary.TButton', background=[('active', self.colors['primary_dark']), ('pressed', self.colors['primary_dark']), ('disabled', '#555555')])
        
        style.configure('Secondary.TButton', font=self.fonts['button'], foreground='white', background=self.colors['secondary'], borderwidth=0, focuscolor='none')
        style.map('Secondary.TButton', background=[('active', self.colors['secondary_dark']), ('pressed', self.colors['secondary_dark']), ('disabled', '#555555')])
        
        style.configure('Danger.TButton', font=self.fonts['button'], foreground='white', background=self.colors['danger'], borderwidth=0, focuscolor='none')
        style.map('Danger.TButton', background=[('active', self.colors['danger_dark']), ('pressed', self.colors['danger_dark']), ('disabled', '#555555')])
        
        style.configure('Default.TButton', font=self.fonts['button'], foreground=self.colors['text'], background=self.colors['surface_dark'], borderwidth=1, bordercolor=self.colors['border'], focuscolor='none')
        style.map('Default.TButton', background=[('active', self.colors['hover']), ('pressed', self.colors['hover']), ('disabled', self.colors['surface_dark'])])
        
        # 配置Entry样式
        style.configure('Custom.TEntry', fieldbackground=self.colors['surface_dark'], bordercolor=self.colors['border'], lightcolor=self.colors['border'], darkcolor=self.colors['border'], borderwidth=1, relief='solid', foreground=self.colors['text'], insertcolor=self.colors['primary'])
        style.map('Custom.TEntry', fieldbackground=[('focus', self.colors['surface_dark'])], bordercolor=[('focus', self.colors['primary'])], lightcolor=[('focus', self.colors['primary'])], darkcolor=[('focus', self.colors['primary'])])
        
        # 配置Checkbutton样式
        style.configure('Custom.TCheckbutton', font=self.fonts['body'], background=self.colors['surface'], foreground=self.colors['text'], indicatorbackground=self.colors['surface_dark'], indicatorforeground=self.colors['primary'], indicatorrelief='solid', bordercolor=self.colors['border'])
        style.map('Custom.TCheckbutton', indicatorcolor=[('selected', self.colors['primary']), ('!selected', self.colors['border'])], background=[('active', self.colors['hover'])])
        
        # 配置Menubutton样式
        style.configure('Custom.TMenubutton', font=self.fonts['button'], background=self.colors['surface_dark'], foreground=self.colors['text'], bordercolor=self.colors['border'], relief='solid', borderwidth=1)
        style.map('Custom.TMenubutton', background=[('active', self.colors['hover']), ('pressed', self.colors['hover'])])
        
        # 配置Scrollbar样式
        style.configure('Custom.Vertical.TScrollbar', background=self.colors['border'], bordercolor=self.colors['border'], troughcolor=self.colors['surface'], arrowcolor=self.colors['text_secondary'], gripcount=0, relief='flat')
        style.map('Custom.Vertical.TScrollbar', background=[('active', self.colors['text_secondary'])])
        
        style.configure('Custom.Horizontal.TScrollbar', background=self.colors['border'], bordercolor=self.colors['border'], troughcolor=self.colors['surface'], arrowcolor=self.colors['text_secondary'], gripcount=0, relief='flat')
        style.map('Custom.Horizontal.TScrollbar', background=[('active', self.colors['text_secondary'])])

def main():
    root = tk.Tk()
    app = FarmBotGUI(root)
    
    print("快捷键绑定完成")
    root.mainloop()

if __name__ == "__main__":
    main()