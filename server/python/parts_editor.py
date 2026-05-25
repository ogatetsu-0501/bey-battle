import json
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

PARTS_JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "parts.json"
JAVA_SOURCE_DIR_PATH = Path(__file__).resolve().parent.parent / "java" / "src"
FRONTEND_API_CONFIG_PATH = Path(__file__).resolve().parents[2] / "src" / "config" / "apiConfig.json"


# --- load_parts_data -----------------------------------------------------------
#【呼ばれる場面】GUI起動直後または保存後再読込時に、最新JSONをメモリへ展開するときに呼ばれる。
#【すること】JSONファイルを読み込み、編集に必要なpartTypesとpartsを返し、フォーマット不整合時は例外を送出する。
#【入力】json_path（パーツJSONファイルパス（Path））
#【出力】パーツ全体データ（dict）
#【外部境界】ファイル読み込み（Path.read_text）
# -------------------------------------------------------------------------------
def load_parts_data(json_path: Path) -> dict:
    return json.loads(json_path.read_text(encoding="utf-8"))


# --- validate_parts_data --------------------------------------------------------
#【呼ばれる場面】保存実行直前に、永続化してよい構造かを判定するときに呼ばれる。
#【すること】必須キー、partTypes整合、requiredParts参照先の妥当性を検証し、違反があれば人が読めるエラー一覧を返す。
#【入力】data（検証対象JSONデータ（dict））
#【出力】検証エラーメッセージ一覧（list[str]）
#【外部境界】なし
# -------------------------------------------------------------------------------
def validate_parts_data(data: dict) -> list[str]:
    errors: list[str] = []
    if "partTypes" not in data or not isinstance(data["partTypes"], list):
        errors.append("partTypes が存在しないか、配列ではありません。")
        return errors
    if "parts" not in data or not isinstance(data["parts"], dict):
        errors.append("parts が存在しないか、オブジェクトではありません。")
        return errors

    part_types = data["partTypes"]
    parts = data["parts"]

    for part_type in part_types:
        if part_type not in parts:
            errors.append(f"parts.{part_type} が存在しません。")
            continue
        if not isinstance(parts[part_type], list):
            errors.append(f"parts.{part_type} は配列である必要があります。")
            continue

        for index, item in enumerate(parts[part_type]):
            if not isinstance(item, dict):
                errors.append(f"parts.{part_type}[{index}] はオブジェクトである必要があります。")
                continue
            if "name" not in item or not isinstance(item["name"], str) or item["name"].strip() == "":
                errors.append(f"parts.{part_type}[{index}] の name が不正です。")
            if "requiredParts" not in item or not isinstance(item["requiredParts"], list):
                errors.append(f"parts.{part_type}[{index}] の requiredParts が不正です。")
                continue
            for required_part in item["requiredParts"]:
                if required_part not in part_types:
                    errors.append(
                        f"parts.{part_type}[{index}].requiredParts に未定義パーツ種別 {required_part} があります。"
                    )
    return errors


# --- save_parts_data ------------------------------------------------------------
#【呼ばれる場面】ユーザーが保存ボタンを押し、検証に通過した編集結果を永続化するときに呼ばれる。
#【すること】UTF-8整形JSONとして上書き保存し、書き込み失敗時は呼び出し元へ例外を返して通知処理へ分岐させる。
#【入力】json_path（保存先パス（Path））, data（保存データ（dict））
#【出力】なし（void）
#【外部境界】ファイル書き込み（Path.write_text）
# -------------------------------------------------------------------------------
def save_parts_data(json_path: Path, data: dict) -> None:
    # 永続化失敗は編集内容喪失に直結するため、例外を握りつぶさず上位へ伝播する。
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# --- save_frontend_api_config ---------------------------------------------------
#【呼ばれる場面】Java APIの待受先をGUIで確定し、フロントの取得先設定を同期するときに呼ばれる。
#【すること】指定URLをapiConfig.jsonへ保存し、次回フロント起動時に同じアドレスへアクセスできるようにする。
#【入力】config_path（設定保存先パス（Path））, parts_api_url（パーツAPI完全URL（string））
#【出力】なし（void）
#【外部境界】ファイル書き込み（Path.write_text）
# -------------------------------------------------------------------------------
def save_frontend_api_config(config_path: Path, parts_api_url: str) -> None:
    # 設定更新に失敗するとフロントが旧API先へ接続し続けるため、必ず例外を上位へ伝播する。
    config_path.write_text(json.dumps({"partsApiUrl": parts_api_url}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class PartsEditorApp:
    # --- __init__ ------------------------------------------------------------------
    #【呼ばれる場面】GUIアプリ初期化時にインスタンス生成されるときに呼ばれる。
    #【すること】データ読込、UI部品生成、イベント紐付けを行い、種別選択と一覧表示の初期状態を確立する。
    #【入力】root（Tkルートウィンドウ（tk.Tk））
    #【出力】なし（void）
    #【外部境界】Tkinterウィジェット生成、ファイル読み込み
    # -------------------------------------------------------------------------------
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Bey Parts JSON Editor")
        self.data = load_parts_data(PARTS_JSON_PATH)

        self.part_type_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.api_host_var = tk.StringVar(value="localhost")
        self.api_port_var = tk.StringVar(value="8080")
        self.api_status_var = tk.StringVar(value="停止中")
        self.required_parts_vars: dict[str, tk.BooleanVar] = {}
        self.api_process: subprocess.Popen[bytes] | None = None

        self.create_widgets()
        self.refresh_part_types()

    # --- create_widgets ------------------------------------------------------------
    #【呼ばれる場面】初期化時に編集UI一式を構築するときに呼ばれる。
    #【すること】種別選択、一覧、入力欄、操作ボタンを配置し、ユーザーが追加/編集/削除/保存とAPI起動制御をできる画面を作る。
    #【入力】なし
    #【出力】なし（void）
    #【外部境界】Tkinterウィジェット生成
    # -------------------------------------------------------------------------------
    def create_widgets(self) -> None:
        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(main_frame, text="パーツ種別").grid(row=0, column=0, sticky="w")
        self.part_type_combo = ttk.Combobox(main_frame, textvariable=self.part_type_var, state="readonly")
        self.part_type_combo.grid(row=0, column=1, sticky="ew")
        self.part_type_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_items())

        self.items_listbox = tk.Listbox(main_frame, height=12)
        self.items_listbox.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=8)
        self.items_listbox.bind("<<ListboxSelect>>", lambda _event: self.load_selected_item())

        ttk.Label(main_frame, text="名前").grid(row=2, column=0, sticky="w")
        ttk.Entry(main_frame, textvariable=self.name_var).grid(row=2, column=1, sticky="ew")

        self.required_parts_frame = ttk.LabelFrame(main_frame, text="requiredParts")
        self.required_parts_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=8)

        parts_buttons_frame = ttk.Frame(main_frame)
        parts_buttons_frame.grid(row=4, column=0, columnspan=2, sticky="ew")
        ttk.Button(parts_buttons_frame, text="追加", command=self.add_item).grid(row=0, column=0, padx=4)
        ttk.Button(parts_buttons_frame, text="編集反映", command=self.update_item).grid(row=0, column=1, padx=4)
        ttk.Button(parts_buttons_frame, text="削除", command=self.delete_item).grid(row=0, column=2, padx=4)
        ttk.Button(parts_buttons_frame, text="保存", command=self.save_all).grid(row=0, column=3, padx=4)

        api_frame = ttk.LabelFrame(main_frame, text="Java API制御")
        api_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=8)
        ttk.Label(api_frame, text="ホスト").grid(row=0, column=0, sticky="w")
        ttk.Entry(api_frame, textvariable=self.api_host_var).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Label(api_frame, text="ポート").grid(row=0, column=2, sticky="w")
        ttk.Entry(api_frame, textvariable=self.api_port_var, width=8).grid(row=0, column=3, sticky="w", padx=4)
        ttk.Button(api_frame, text="API起動", command=self.start_api).grid(row=1, column=0, padx=4, pady=4)
        ttk.Button(api_frame, text="API停止", command=self.stop_api).grid(row=1, column=1, padx=4, pady=4)
        ttk.Button(api_frame, text="アドレス設定だけ反映", command=self.apply_api_address_config).grid(row=1, column=2, columnspan=2, padx=4, pady=4)
        ttk.Label(api_frame, textvariable=self.api_status_var).grid(row=2, column=0, columnspan=4, sticky="w")
        api_frame.columnconfigure(1, weight=1)

        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # --- build_parts_api_url -------------------------------------------------------
    #【呼ばれる場面】API起動時または設定反映時に、フロント向けの完全URLを組み立てるときに呼ばれる。
    #【すること】ホスト入力とポート入力を検証し、問題がなければ`http://host:port/api/parts`を返す。
    #【入力】なし
    #【出力】API URL（string）
    #【外部境界】なし
    # -------------------------------------------------------------------------------
    def build_parts_api_url(self) -> str:
        host = self.api_host_var.get().strip()
        port = self.api_port_var.get().strip()
        if host == "":
            raise ValueError("ホストは必須です。")
        if not port.isdigit():
            raise ValueError("ポートは数値で入力してください。")
        return f"http://{host}:{port}/api/parts"

    # --- apply_api_address_config --------------------------------------------------
    #【呼ばれる場面】APIアドレス変更をフロント側設定へ同期したいときに呼ばれる。
    #【すること】入力中のホスト/ポートからURLを生成してapiConfig.jsonへ保存し、成功時は状態表示を更新する。
    #【入力】なし
    #【出力】なし（void）
    #【外部境界】ファイル書き込み、Tkinterメッセージ表示
    # -------------------------------------------------------------------------------
    def apply_api_address_config(self) -> None:
        try:
            parts_api_url = self.build_parts_api_url()
            save_frontend_api_config(FRONTEND_API_CONFIG_PATH, parts_api_url)
            self.api_status_var.set(f"API設定反映済み: {parts_api_url}")
            messagebox.showinfo("設定反映", f"フロント設定を更新しました。\n{parts_api_url}")
        except (OSError, ValueError) as error:
            messagebox.showerror("設定失敗", str(error))

    # --- start_api -----------------------------------------------------------------
    #【呼ばれる場面】ユーザーがAPI起動ボタンを押し、Java APIをGUIから立ち上げるときに呼ばれる。
    #【すること】未起動時のみjavac→javaを順に実行し、起動成功後にフロント設定URLを保存して状態表示へ反映する。
    #【入力】なし
    #【出力】なし（void）
    #【外部境界】外部プロセス起動（subprocess）、ファイル書き込み、Tkinterメッセージ表示
    # -------------------------------------------------------------------------------
    def start_api(self) -> None:
        if self.api_process and self.api_process.poll() is None:
            messagebox.showinfo("情報", "APIは既に起動しています。")
            return

        try:
            parts_api_url = self.build_parts_api_url()
            host = self.api_host_var.get().strip()
            port = self.api_port_var.get().strip()
            subprocess.run(["javac", "PartsApiServer.java"], cwd=JAVA_SOURCE_DIR_PATH, check=True)
            self.api_process = subprocess.Popen(["java", "PartsApiServer", host, port], cwd=JAVA_SOURCE_DIR_PATH)
            save_frontend_api_config(FRONTEND_API_CONFIG_PATH, parts_api_url)
            self.api_status_var.set(f"起動中: {parts_api_url}")
        except (subprocess.SubprocessError, OSError, ValueError) as error:
            self.api_process = None
            messagebox.showerror("API起動失敗", str(error))

    # --- stop_api ------------------------------------------------------------------
    #【呼ばれる場面】ユーザーがAPI停止ボタンを押し、起動済みJava APIを終了させるときに呼ばれる。
    #【すること】起動中プロセスへ終了要求を送り、一定時間で停止しない場合は強制終了して状態を停止へ更新する。
    #【入力】なし
    #【出力】なし（void）
    #【外部境界】外部プロセス終了（subprocess）、Tkinterメッセージ表示
    # -------------------------------------------------------------------------------
    def stop_api(self) -> None:
        if not self.api_process or self.api_process.poll() is not None:
            self.api_process = None
            self.api_status_var.set("停止中")
            return

        try:
            # 停止失敗でプロセスが残るとポート競合や誤接続の運用事故になるため、timeout後に強制終了する。
            self.api_process.terminate()
            self.api_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.api_process.kill()
            self.api_process.wait(timeout=5)
        finally:
            self.api_process = None
            self.api_status_var.set("停止中")

    # --- on_close ------------------------------------------------------------------
    #【呼ばれる場面】ウィンドウを閉じる操作でアプリ終了処理が必要になったときに呼ばれる。
    #【すること】起動中APIを停止して孤児プロセスを防ぎ、その後GUIを安全に終了する。
    #【入力】なし
    #【出力】なし（void）
    #【外部境界】外部プロセス終了、Tkinterウィンドウ破棄
    # -------------------------------------------------------------------------------
    def on_close(self) -> None:
        self.stop_api()
        self.root.destroy()

    def refresh_part_types(self) -> None:
        part_types = self.data["partTypes"]
        self.part_type_combo["values"] = part_types
        if part_types:
            self.part_type_var.set(part_types[0])
        self.refresh_required_parts_checkboxes()
        self.refresh_items()

    def refresh_required_parts_checkboxes(self) -> None:
        for child in self.required_parts_frame.winfo_children():
            child.destroy()
        self.required_parts_vars.clear()
        for row_index, part_type in enumerate(self.data["partTypes"]):
            var = tk.BooleanVar(value=False)
            self.required_parts_vars[part_type] = var
            ttk.Checkbutton(self.required_parts_frame, text=part_type, variable=var).grid(row=row_index // 3, column=row_index % 3, sticky="w")

    def refresh_items(self) -> None:
        part_type = self.part_type_var.get()
        self.items_listbox.delete(0, tk.END)
        for item in self.data["parts"].get(part_type, []):
            self.items_listbox.insert(tk.END, item["name"])
        self.clear_form()

    def load_selected_item(self) -> None:
        selected_indices = self.items_listbox.curselection()
        if not selected_indices:
            return
        selected_index = selected_indices[0]
        part_type = self.part_type_var.get()
        item = self.data["parts"][part_type][selected_index]
        self.name_var.set(item["name"])
        for required_part, var in self.required_parts_vars.items():
            var.set(required_part in item["requiredParts"])

    def build_form_item(self) -> dict:
        required_parts = [part_type for part_type, var in self.required_parts_vars.items() if var.get()]
        return {
            "name": self.name_var.get().strip(),
            "requiredParts": required_parts,
        }

    def add_item(self) -> None:
        part_type = self.part_type_var.get()
        item = self.build_form_item()
        if item["name"] == "":
            messagebox.showerror("入力エラー", "名前は必須です。")
            return
        self.data["parts"][part_type].append(item)
        self.refresh_items()

    def update_item(self) -> None:
        selected_indices = self.items_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("選択エラー", "編集対象を選択してください。")
            return
        item = self.build_form_item()
        if item["name"] == "":
            messagebox.showerror("入力エラー", "名前は必須です。")
            return
        part_type = self.part_type_var.get()
        self.data["parts"][part_type][selected_indices[0]] = item
        self.refresh_items()

    def delete_item(self) -> None:
        selected_indices = self.items_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("選択エラー", "削除対象を選択してください。")
            return
        part_type = self.part_type_var.get()
        # 削除は取り消し不能のため、誤選択時にデータ喪失する操作であることを明確にする。
        del self.data["parts"][part_type][selected_indices[0]]
        self.refresh_items()

    def clear_form(self) -> None:
        self.name_var.set("")
        for var in self.required_parts_vars.values():
            var.set(False)

    def save_all(self) -> None:
        errors = validate_parts_data(self.data)
        if errors:
            messagebox.showerror("検証エラー", "\n".join(errors))
            return
        try:
            save_parts_data(PARTS_JSON_PATH, self.data)
            messagebox.showinfo("保存完了", f"{PARTS_JSON_PATH} に保存しました。")
        except OSError as error:
            messagebox.showerror("保存失敗", str(error))


# --- main ----------------------------------------------------------------------
#【呼ばれる場面】Pythonファイルを直接実行したときにエントリーポイントとして呼ばれる。
#【すること】Tkルートを生成して編集アプリを初期化し、イベントループを開始してGUI操作を受け付ける。
#【入力】なし
#【出力】なし（void）
#【外部境界】Tkinterイベントループ
# -------------------------------------------------------------------------------
def main() -> None:
    root = tk.Tk()
    PartsEditorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
