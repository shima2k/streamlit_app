# app.py
import streamlit as st
import qrcode
import pandas as pd
from datetime import datetime
import cv2
import os
import time
import re
from remember import save_login_info, load_login_info
# ===================== CẤU HÌNH TRANG =====================
st.set_page_config(page_title="Điểm danh QR", page_icon="🎓", layout="wide")
st.title("🎓 HỆ THỐNG ĐIỂM DANH BẰNG MÃ QR")
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import cv2

class VideoTransformer(VideoTransformerBase):
    def transform(self, frame):
        # Chỉnh sửa hoặc xử lý video nếu cần
        return frame

webrtc_streamer(key="qr_code_scanner", video_transformer_factory=VideoTransformer)

def auto_login():
    """Tự động đăng nhập lại nếu có thông tin ghi nhớ"""
    if "user" not in st.session_state:
        remembered = load_login_info()
        uname = remembered.get("username", "")
        pwd = remembered.get("password", "")

        if uname:  # chỉ cần username là đủ
            teachers = read_teachers()
            row = teachers[teachers["username"] == uname]
            if not row.empty:
                row = row.iloc[0]
                if bool(row.get("active", True)):
                    # Nếu có password thì kiểm tra, nếu không có thì bỏ qua
                    if not pwd or str(row["password"]) == pwd:
                        st.session_state["user"] = {
                            "username": row["username"],
                            "fullname": row["fullname"],
                            "role": row["role"]
                        }

TEACHERS_CSV = "teachers.csv"
SUBJECTS_CSV = "subjects.csv"
QR_DIR = "qr_codes"

# ===================== HÀM TIỆN ÍCH =====================
def ensure_csv_files():
    # Tạo superadmin mặc định nếu chưa có file
    if not os.path.exists(TEACHERS_CSV):
        df = pd.DataFrame([
            {"username": "superadmin", "password": "123456", "fullname": "Quản trị viên tổng", "role": "superadmin", "active": True}
        ])
        df.to_csv(TEACHERS_CSV, index=False)
    if not os.path.exists(SUBJECTS_CSV):
        pd.DataFrame(columns=["teacher_username", "subject_name"]).to_csv(SUBJECTS_CSV, index=False)
    os.makedirs(QR_DIR, exist_ok=True)

def read_teachers():
    df = pd.read_csv(TEACHERS_CSV)
    # chuẩn hóa cột active về bool
    if "active" in df.columns:
        df["active"] = df["active"].astype(str).str.lower().isin(["true", "1", "yes"])
    return df

def write_teachers(df):
    df.to_csv(TEACHERS_CSV, index=False)


import pandas as pd
import os

def read_subjects():
    if not os.path.exists(SUBJECTS_CSV):
        ensure_csv_files()
    df = pd.read_csv(SUBJECTS_CSV, dtype=str)
    df = df.fillna("")
    return df

def save_subjects(df):
    df = df.fillna("")
    df.to_csv(SUBJECTS_CSV, index=False)





def write_subjects(df):
    df.to_csv(SUBJECTS_CSV, index=False)

def slugify(text):
    """Chuyển text thành dạng an toàn để đặt tên file."""
    text = str(text or "").strip().replace(" ", "_")
    return "".join(c for c in text if c.isalnum() or c in ("_", "-"))


def attendance_filename(subject_name: str, teacher_username: str) -> str:
    return f"attendance_{slugify(subject_name)}_{slugify(teacher_username)}.csv"

def is_logged_in():
    return "user" in st.session_state and st.session_state["user"] is not None

def logout():
    from remember import save_login_info  # import ngay trong hàm để tránh lỗi vòng lặp import
    save_login_info("", "")  # Xóa thông tin ghi nhớ khi đăng xuất
    st.session_state.pop("user", None)
    st.session_state.pop("subject", None)
    st.session_state.pop("attendance_file", None)

ensure_csv_files()

# ===================== ĐĂNG NHẬP =====================
def login_view():
    st.subheader("🔐 Đăng nhập")

    # --- Tải thông tin đã ghi nhớ (nếu có) ---
    remembered = load_login_info()
    default_username = remembered.get("username", "")
    default_password = remembered.get("password", "")

    # --- Form đăng nhập ---
    with st.form("login_form_unique"):  # Đổi key để tránh lỗi trùng
        username = st.text_input("Tên đăng nhập", value=default_username)
        password = st.text_input("Mật khẩu", type="password", value=default_password)
        remember_me = st.checkbox("💾 Ghi nhớ đăng nhập", value=bool(default_username))
        submit = st.form_submit_button("Đăng nhập")

    if submit:
        teachers = read_teachers()
        row = teachers[teachers["username"] == username]
        if row.empty:
            st.error("❌ Tài khoản không tồn tại.")
            return
        row = row.iloc[0]
        if not bool(row.get("active", True)):
            st.error("🚫 Tài khoản đã bị vô hiệu hóa.")
            return
        if str(row["password"]) != password:
            st.error("❌ Mật khẩu không đúng.")
            return

        # ✅ Nếu chọn “Ghi nhớ đăng nhập”, lưu lại thông tin
        if remember_me:
            save_login_info(username, password)   # lưu user + pass
        else:
            save_login_info(username, "")         # chỉ lưu user thôi, không lưu pass


        st.session_state["user"] = {
            "username": row["username"],
            "fullname": row["fullname"],
            "role": row["role"]
        }
        st.success(f"✅ Xin chào, {row['fullname']}!")
        if "user" in st.session_state:
            st.session_state["keep_user"] = st.session_state["user"]

        st.rerun()

# ===================== MENU CHÍNH =====================
def main_menu():
    user = st.session_state["user"]
    col1, col2 = st.columns([6, 1])

    with col1:
        st.write(f"👋 Xin chào, **{user['fullname']}** ({user['role']})")

    with col2:
        with st.popover("⚙️", use_container_width=False):
            st.write(f"👋 Xin chào, **{user['fullname']}**")
            if st.button("🔑 Đổi mật khẩu", use_container_width=True):
                st.session_state["show_self_change"] = True
                if "user" in st.session_state:
                    st.session_state["keep_user"] = st.session_state["user"]

                st.rerun()
            if st.button("🚪 Đăng xuất", use_container_width=True):
                logout()
                if "user" in st.session_state:
                    st.session_state["keep_user"] = st.session_state["user"]

                st.rerun()

            st.markdown(
                f"""
                <style>
                div[data-testid="stHorizontalBlock"] div[data-testid="column"]:last-child {{
                    text-align: right;
                }}
                .dropdown {{
                    position: relative;
                    display: inline-block;
                }}
                .dropdown-content {{
                    display: none;
                    position: absolute;
                    right: 0;
                    background-color: white;
                    min-width: 180px;
                    border-radius: 8px;
                    box-shadow: 0px 4px 10px rgba(0,0,0,0.15);
                    z-index: 100;
                }}
                .dropdown-content a {{
                    color: black;
                    padding: 10px 16px;
                    text-decoration: none;
                    display: block;
                }}
                .dropdown-content a:hover {{
                    background-color: #f2f2f2;
                }}
                .dropdown:hover .dropdown-content {{
                    display: block;
                }}
                </style>
                <div class="dropdown">
                    <button style="background:none;border:none;font-size:20px;cursor:pointer;">⚙️</button>
                    <div class="dropdown-content">
                        <a>👋 Xin chào, <b>{user['fullname']}</b></a>
                        <a href="#">🔑 Đổi mật khẩu</a>
                        
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if user["role"] in ["admin", "superadmin"]:
        tabs = st.tabs(["🏷️ Tạo QR", "📸 Điểm danh", "📅 Thống kê", "👨‍🏫 Quản lý người dùng", "📚 Quản lý môn"])
        with tabs[0]:
            view_admin_qr()
        with tabs[1]:
            view_attendance(user, admin_impersonate=True)
        with tabs[2]:
            view_statistics(user, admin_view_all=True)
        with tabs[3]:
            view_manage_teachers()
        with tabs[4]:
            view_manage_subjects(admin_mode=True)
    else:
        tabs = st.tabs(["📸 Điểm danh", "📅 Thống kê", "📚 Môn của tôi"])
        with tabs[0]:
            view_attendance(user["username"], admin_impersonate=False)

        with tabs[1]:
            view_statistics(user, admin_view_all=False)
        with tabs[2]:
            view_manage_subjects(admin_mode=False, owner_username=user["username"])
# Popup đổi mật khẩu cho tài khoản đang đăng nhập
if st.session_state.get("show_self_change", False):
    st.markdown("### 🔒 Đổi mật khẩu của bạn")
    old_pass = st.text_input("🔑 Mật khẩu cũ", type="password", key="old_self_pass")
    new_pass = st.text_input("🆕 Mật khẩu mới", type="password", key="new_self_pass")
    confirm = st.text_input("🔁 Nhập lại mật khẩu", type="password", key="confirm_self_pass")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Lưu thay đổi"):
            teachers = read_teachers()
            user_row = teachers[teachers["username"] == st.session_state["user"]["username"]]
            if user_row.empty:
                st.error("Không tìm thấy tài khoản.")
            elif str(user_row.iloc[0]["password"]) != old_pass:
                st.error("❌ Mật khẩu cũ không đúng.")
            elif not new_pass or new_pass != confirm:
                st.warning("⚠️ Mật khẩu mới không khớp.")
            else:
                teachers.loc[teachers["username"] == st.session_state["user"]["username"], "password"] = new_pass
                write_teachers(teachers)
                st.success("✅ Đổi mật khẩu thành công!")
                time.sleep(1.2)
                st.session_state["show_self_change"] = False
                if "user" in st.session_state:
                    st.session_state["keep_user"] = st.session_state["user"]

                st.rerun()
    with c2:
        if st.button("❌ Hủy"):
            st.session_state["show_self_change"] = False
            if "user" in st.session_state:
                st.session_state["keep_user"] = st.session_state["user"]

            st.rerun()

# ===================== ADMIN/SUPERADMIN: TẠO QR =====================
def view_admin_qr():
    st.subheader("🏷️ Tạo mã QR cho học sinh (chỉ admin/superadmin)")
    name = st.text_input("Tên học sinh")
    student_id = st.text_input("Mã học sinh (VD: HS001)")
    classroom = st.text_input("Lớp (VD: 10A1)")
    if st.button("🎁 Tạo mã QR"):
        if not (name and student_id and classroom):
            st.warning("⚠️ Vui lòng nhập đủ thông tin.")
            return
        data = f"{student_id} - {name} - {classroom}"
        img = qrcode.make(data)
        path = os.path.join(QR_DIR, f"{slugify(student_id)}_{slugify(name)}.png")
        img.save(path)
        st.image(path, caption=f"Mã QR của {name}", width=250)
        with open(path, "rb") as f:
            st.download_button("⬇️ Tải mã QR", f, file_name=os.path.basename(path))
        st.success("✅ Đã tạo QR.")

# ===================== ADMIN/SUPERADMIN: QUẢN LÝ NGƯỜI DÙNG =====================
def view_manage_teachers():
    st.subheader("👨‍🏫 Quản lý tài khoản giáo viên & quản trị")

    current_role = st.session_state["user"]["role"]
    current_user = st.session_state["user"]["username"]

    # Hiển thị thông báo sau reload (nếu có)
    if "message" in st.session_state:
        # cho phép các icon khác nhau: bắt đầu chuỗi bằng [type]: message (success, info, warning, error)
        msg = st.session_state["message"]
        if isinstance(msg, tuple) and len(msg) == 2:
            level, text = msg
            if level == "success": st.success(text)
            elif level == "warning": st.warning(text)
            elif level == "error": st.error(text)
            else: st.info(text)
        else:
            st.success(msg)
        del st.session_state["message"]

    df = read_teachers()
    tab1, tab2, tab3 = st.tabs(["📋 Danh sách", "➕ Thêm tài khoản", "⚙️ Quản lý trạng thái"])

    # --- TAB 1: DANH SÁCH ---
    # --- TAB 1: DANH SÁCH ---
    with tab1:
        st.markdown("### 📋 Danh sách người dùng")

        df = read_teachers().reset_index(drop=True)
        current_user = st.session_state["user"]["username"]
        current_role = st.session_state["user"]["role"]

        for i in range(len(df)):
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2, 2, 2, 2, 1.5, 1.5])
            username = df.loc[i, "username"]
            fullname = df.loc[i, "fullname"]
            role = df.loc[i, "role"]

            with col1:
                st.write(username)
            with col2:
                st.write(fullname)
            with col3:
                # Hiện hoặc ẩn mật khẩu
                key_show = f"show_pass_{i}"
                if key_show not in st.session_state:
                    st.session_state[key_show] = False

                if st.session_state[key_show]:
                    st.text(df.loc[i, "password"])
                else:
                    st.text("•" * len(str(df.loc[i, "password"])))

            with col4:
                # Nút hiện / ẩn mật khẩu
                if st.button("👁️ Hiện" if not st.session_state[key_show] else "🙈 Ẩn", key=f"btn_show_{i}"):
                    st.session_state[key_show] = not st.session_state[key_show]
                    if "user" in st.session_state:
                        st.session_state["keep_user"] = st.session_state["user"]

                    st.rerun()

            with col5:
                st.write(role)
            with col6:
                st.checkbox("Hoạt động", value=bool(df.loc[i, "active"]), disabled=True, key=f"active_{i}")

            with col7:
                # Kiểm tra quyền được phép đổi mật khẩu
                can_change = False
                if current_user == username:
                    can_change = True
                elif current_role == "admin" and role == "teacher":
                    can_change = True
                elif current_role == "superadmin" and role in ["admin", "teacher"]:
                    can_change = True

                if can_change:
                    if st.button("🔑 Đổi mật khẩu", key=f"btn_change_{i}"):
                        st.session_state["target_user_change"] = username
                        st.session_state["target_fullname"] = fullname
                        st.session_state["target_role"] = role
                        st.session_state["show_change_popup"] = True
                        if "user" in st.session_state:
                            st.session_state["keep_user"] = st.session_state["user"]

                        st.rerun()
                else:
                    st.write("—")

        # =================== POPUP ĐỔI MẬT KHẨU ===================
        # =================== POPUP GIẢ LẬP (tương thích mọi phiên bản) ===================
        if st.session_state.get("show_change_popup", False):
            target_user = st.session_state.get("target_user_change", "")
            target_fullname = st.session_state.get("target_fullname", "")
            target_role = st.session_state.get("target_role", "")

            st.markdown("---")
            st.markdown(f"### 🔒 Đổi mật khẩu cho **{target_user}**")
            st.info(f"👤 **{target_fullname}**  📘 Vai trò: **{target_role}**")

            new_pass = st.text_input("🔑 Nhập mật khẩu mới", type="password", key="new_pass_input")
            confirm_pass = st.text_input("🔁 Nhập lại mật khẩu", type="password", key="confirm_pass_input")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Lưu thay đổi", key=f"save_change_{target_user}"):

                    if not new_pass or not confirm_pass:
                        st.warning("⚠️ Vui lòng nhập đầy đủ mật khẩu.")
                    elif new_pass != confirm_pass:
                        st.error("❌ Mật khẩu nhập lại không khớp.")
                    else:
                        df.loc[df["username"] == target_user, "password"] = new_pass
                        write_teachers(df)
                        st.success(f"✅ Đã đổi mật khẩu cho **{target_user}** thành công!")
                        time.sleep(1.5)
                        st.session_state["show_change_popup"] = False
                        if "user" in st.session_state:
                            st.session_state["keep_user"] = st.session_state["user"]

                        st.rerun()
            with c2:
                if st.button("❌ Hủy", key=f"cancel_change_{target_user}"):

                    st.session_state["show_change_popup"] = False
                    if "user" in st.session_state:
                            st.session_state["keep_user"] = st.session_state["user"]

                    st.rerun()


        st.caption("👁️ Bấm 'Hiện' để xem mật khẩu hoặc 🔑 'Đổi mật khẩu' nếu có quyền.")

    # --- TAB 2: THÊM NGƯỜI DÙNG ---
    with tab2:
        st.markdown("### ➕ Thêm tài khoản mới")
        with st.form("add_user"):
            u = st.text_input("Tên đăng nhập")
            p = st.text_input("Mật khẩu", type="password")
            fn = st.text_input("Họ tên")
            role_options = ["teacher", "admin"]
            if current_role == "superadmin":
                role_options.append("superadmin")
            role = st.selectbox("Vai trò", role_options)
            active = st.checkbox("Kích hoạt", True)
            sub = st.form_submit_button("Thêm")

        if sub:
            if not (u and p and fn):
                st.warning("⚠️ Điền đủ thông tin.")
            elif (df["username"] == u).any():
                st.error("❌ Username đã tồn tại.")
            else:
                df.loc[len(df)] = {"username": u, "password": p, "fullname": fn, "role": role, "active": active}
                write_teachers(df)
                st.session_state["message"] = ("success", f"✅ Đã thêm tài khoản **{fn} ({u})** với vai trò **{role}**!")
                if "user" in st.session_state:
                    st.session_state["keep_user"] = st.session_state["user"]

                st.rerun()

    # --- TAB 3: QUẢN LÝ TRẠNG THÁI ---
    with tab3:
        st.markdown("### ⚙️ Kích hoạt / Vô hiệu hóa / Xóa tài khoản")
        with st.form("modify_user"):
            all_users = df["username"].tolist()
            target = st.selectbox("Chọn tài khoản", all_users)
            action = st.selectbox("Hành động", ["Kích hoạt", "Vô hiệu hóa", "Xóa"])
            sub2 = st.form_submit_button("Thực hiện")

        if sub2:
            if target == current_user:
                st.error("🚫 Không thể thao tác chính mình.")
                return

            target_role = df.loc[df["username"] == target, "role"].values[0]
            target_name = df.loc[df["username"] == target, "fullname"].values[0]

            # Quyền hạn:
            if st.session_state["user"]["role"] == "admin":
                # admin thường không được thao tác với admin/superadmin
                if target_role in ["admin", "superadmin"]:
                    st.error("🚫 Admin không thể thao tác với admin khác hoặc superadmin.")
                    return
            elif st.session_state["user"]["role"] == "superadmin":
                # superadmin có quyền xóa admin khác, nhưng không được động vào chính superadmin
                if target == "superadmin":
                    st.error("🚫 Không thể thao tác tài khoản superadmin chính.")
                    return

            # Thực hiện
            if action == "Xóa":
                df = df[df["username"] != target]
                msg = ("success", f"🗑️ Đã xóa tài khoản **{target_name} ({target})**.")
            elif action == "Vô hiệu hóa":
                df.loc[df["username"] == target, "active"] = False
                msg = ("warning", f"🚫 Đã vô hiệu hóa tài khoản **{target_name} ({target})**.")
            elif action == "Kích hoạt":
                df.loc[df["username"] == target, "active"] = True
                msg = ("success", f"✅ Đã kích hoạt lại tài khoản **{target_name} ({target})**.")

            write_teachers(df)
            st.session_state["message"] = msg
            if "user" in st.session_state:
                st.session_state["keep_user"] = st.session_state["user"]

            st.rerun()

# ===================== QUẢN LÝ MÔN HỌC (THÊM/SỬA/XÓA + THÔNG BÁO) =====================
def view_manage_subjects(admin_mode=False, owner_username=None):
    st.subheader("📚 Quản lý môn học")

    # Hiển thị thông báo sau thao tác (nếu có)
    if "subject_message" in st.session_state:
        msg = st.session_state["subject_message"]
        if isinstance(msg, tuple) and len(msg) == 2:
            level, text = msg
            getattr(st, level)(text)
        else:
            st.success(msg)
        del st.session_state["subject_message"]

    sub_df = read_subjects()
    tch_df = read_teachers()

    # ================= ADMIN / SUPERADMIN =================
    if admin_mode:
        tabs = st.tabs(["📋 Danh sách môn học", "➕ Thêm môn học mới"])

        # --- TAB 1: DANH SÁCH ---
        with tabs[0]:
            st.markdown("### 📋 Danh sách tất cả môn học")

            if sub_df.empty:
                st.info("Hiện chưa có môn học nào.")
            else:
                sub_df = sub_df.copy()
                sub_df["Chọn"] = False

                edited_df = st.data_editor(
                    sub_df,
                    num_rows="fixed",
                    use_container_width=True,
                    key="edit_subjects_with_check",
                )

                colA, colB = st.columns(2)
                with colA:
                    if st.button("💾 Lưu thay đổi"):
                        to_save = edited_df.copy()
                        if "Chọn" in to_save.columns:
                            to_save = to_save.drop(columns=["Chọn"])
                        to_save = to_save.fillna("")
                        to_save = to_save.astype(str)
                        save_subjects(to_save)
                        st.session_state["subject_message"] = ("success", "✅ Đã lưu thay đổi thành công!")
                        if "user" in st.session_state:
                            st.session_state["keep_user"] = st.session_state["user"]

                        st.rerun()

                with colB:
                    if st.button("🗑️ Xóa các dòng đã chọn"):
                        selected_rows = edited_df[edited_df["Chọn"] == True]
                        if selected_rows.empty:
                            st.warning("⚠️ Vui lòng chọn ít nhất một dòng để xóa.")
                        else:
                            remaining_df = edited_df[edited_df["Chọn"] == False].drop(columns=["Chọn"])
                            write_subjects(remaining_df)
                            names = ", ".join(selected_rows["subject_name"].tolist())
                            st.session_state["subject_message"] = ("warning", f"🗑️ Đã xóa các môn: {names}")
                            if "user" in st.session_state:
                                st.session_state["keep_user"] = st.session_state["user"]

                            st.rerun()

        # --- TAB 2: THÊM MÔN ---
        with tabs[1]:
            st.markdown("### ➕ Thêm môn học mới")
            with st.form("add_subject_admin"):
                tu = st.selectbox("👩‍🏫 Giáo viên phụ trách", tch_df["username"].tolist())
                sn = st.text_input("📘 Tên môn mới")
                btn = st.form_submit_button("Thêm")
            if btn:
                if not sn:
                    st.warning("⚠️ Vui lòng nhập tên môn.")
                else:
                    sub_df.loc[len(sub_df)] = {"teacher_username": tu, "subject_name": sn.strip()}
                    write_subjects(sub_df)
                    st.session_state["subject_message"] = ("success", f"✅ Đã thêm môn **{sn}** cho **{tu}**.")
                    if "user" in st.session_state:
                        st.session_state["keep_user"] = st.session_state["user"]

                    st.rerun()

    # ================= GIÁO VIÊN =================
    # ================= GIÁO VIÊN =================
    else:
        tabs = st.tabs(["📋 Danh sách môn học", "➕ Thêm môn học mới"])
        my = sub_df[sub_df["teacher_username"] == owner_username].reset_index(drop=True)

        # --- TAB 1: DANH SÁCH ---
        with tabs[0]:
            st.markdown(f"### 📋 Môn học của **{owner_username}**")
            if len(my):
                my = my.copy()
                my["Chọn"] = False

                edited_df = st.data_editor(
                    my,
                    num_rows="fixed",
                    use_container_width=True,
                    key=f"edit_my_subjects_{owner_username}",
                )

                colA, colB = st.columns(2)
                with colA:
                    if st.button("💾 Lưu thay đổi", key=f"save_subjects_{owner_username}"):
                        to_save = edited_df.drop(columns=["Chọn"])
                        to_save = to_save.fillna("")
                        teacher_rows = sub_df[sub_df["teacher_username"] == owner_username].index.tolist()

                        blocked = []
                        for i, idx in enumerate(teacher_rows):
                            if i < len(to_save):
                                old_name = sub_df.at[idx, "subject_name"].strip()
                                new_name = to_save.loc[i, "subject_name"].strip()
                                if old_name != new_name:
                                    # Kiểm tra file điểm danh tồn tại
                                    attendance_files = [
                                        f for f in os.listdir(os.getcwd())
                                        if f.startswith(f"attendance_{slugify(old_name)}_{owner_username}_") and f.endswith(".csv")
                                    ]
                                    if attendance_files:
                                        blocked.append(old_name)
                                    else:
                                        sub_df.at[idx, "subject_name"] = new_name or old_name

                        write_subjects(sub_df)
                        if blocked:
                            st.warning(f"⚠️ Không thể đổi tên các môn đã có dữ liệu điểm danh: {', '.join(blocked)}")
                        else:
                            st.success("✅ Đã lưu thay đổi thành công!")

                        time.sleep(2)
                        if "user" in st.session_state:
                            st.session_state["keep_user"] = st.session_state["user"]

                        st.rerun()

                with colB:
                    if st.button("🗑️ Xóa các dòng đã chọn", key=f"delete_subjects_{owner_username}"):
                        selected_rows = edited_df[edited_df["Chọn"] == True]
                        if selected_rows.empty:
                            st.warning("⚠️ Vui lòng chọn ít nhất một dòng để xóa.")
                        else:
                            blocked = []
                            for _, row in selected_rows.iterrows():
                                sub_name = row["subject_name"]
                                attendance_files = [
                                    f for f in os.listdir(os.getcwd())
                                    if f.startswith(f"attendance_{slugify(sub_name)}_{owner_username}_") and f.endswith(".csv")
                                ]
                                if attendance_files:
                                    blocked.append(sub_name)

                            if blocked:
                                st.error(f"🚫 Không thể xóa các môn đã có dữ liệu điểm danh: {', '.join(blocked)}")

                            deletable = selected_rows[~selected_rows["subject_name"].isin(blocked)]
                            if not deletable.empty:
                                sub_df = sub_df.drop(
                                    sub_df[
                                        (sub_df["teacher_username"] == owner_username)
                                        & (sub_df["subject_name"].isin(deletable["subject_name"]))
                                    ].index
                                ).reset_index(drop=True)
                                write_subjects(sub_df)
                                names = ", ".join(deletable["subject_name"].tolist())
                                st.success(f"🗑️ Đã xóa các môn: {names}")
                            time.sleep(2)
                            if "user" in st.session_state:
                                st.session_state["keep_user"] = st.session_state["user"]

                            st.rerun()
            else:
                st.info("Bạn chưa có môn học nào.")

        # --- TAB 2: THÊM ---
        with tabs[1]:
            st.markdown("### ➕ Thêm môn học mới")
            with st.form("add_subject_teacher"):
                sn = st.text_input("📘 Tên môn mới")
                btn = st.form_submit_button("Thêm")
            if btn:
                if not sn:
                    st.warning("⚠️ Nhập tên môn.")
                else:
                    sub_df.loc[len(sub_df)] = {"teacher_username": owner_username, "subject_name": sn.strip()}
                    write_subjects(sub_df)
                    st.session_state["subject_message"] = ("success", f"✅ Đã thêm môn **{sn}**.")
                    if "user" in st.session_state:
                            st.session_state["keep_user"] = st.session_state["user"]

                    st.rerun()

# ===================== ĐIỂM DANH =====================


def view_attendance(user, admin_impersonate=False):
    st.subheader("🎥 Điểm danh bằng mã QR")

    # Lấy username giáo viên
    teacher_username = user["username"] if isinstance(user, dict) else user
    teacher_username = str(teacher_username).strip().lower()

    subjects_df = read_subjects()
    teacher_subjects = subjects_df[subjects_df["teacher_username"] == teacher_username]["subject_name"].tolist()

    if not teacher_subjects:
        st.info("Bạn chưa có môn học nào để điểm danh.")
        return

    subject = st.selectbox("📘 Chọn môn học", teacher_subjects)

    # Tạo file điểm danh hôm nay
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"attendance_{slugify(subject)}_{teacher_username}_{today}.csv"
    if not os.path.exists(filename):
        pd.DataFrame(columns=["student_id", "student_name", "class", "timestamp"]).to_csv(filename, index=False)

    df = pd.read_csv(filename)

    # Trạng thái session
    if "scanned_student" not in st.session_state:
        st.session_state["scanned_student"] = None
    if "is_scanning" not in st.session_state:
        st.session_state["is_scanning"] = False

    # Nếu vừa quét xong 1 học sinh → hiển thị popup xác nhận
    if st.session_state["scanned_student"] is not None:
        s = st.session_state["scanned_student"]
        st.success(f"✅ {s['student_name']} ({s['class']}) điểm danh thành công lúc {s['timestamp']}")
        if st.button("OK – Tiếp tục quét"):
            st.session_state["scanned_student"] = None
            st.session_state["is_scanning"] = True
            if "user" in st.session_state:
                st.session_state["keep_user"] = st.session_state["user"]

            st.rerun()
        return

    # Bật camera
    run_camera = st.checkbox("📸 Bật camera điểm danh", value=st.session_state["is_scanning"])

    if run_camera:
        st.session_state["is_scanning"] = True
        cap = cv2.VideoCapture(0)
        detector = cv2.QRCodeDetector()
        stframe = st.empty()
        st.info("👁️ Đưa mã QR của học sinh vào khung hình...")

        while True:
            ret, frame = cap.read()
            if not ret:
                st.warning("⚠️ Không tìm thấy camera.")
                break

            data, bbox, _ = detector.detectAndDecode(frame)
            if data:
                # Dữ liệu QR: "HS001 - Nguyễn Văn A - 10A1"
                parts = re.split(r"[-,]", data)
                parts = [p.strip() for p in parts if p.strip()]
                if len(parts) >= 3:
                    sid, sname, sclass = parts[0], parts[1], parts[2]
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Kiểm tra trùng trong cùng buổi
                    if sid not in df["student_id"].values:
                        new_row = {"student_id": sid, "student_name": sname, "class": sclass, "timestamp": timestamp}
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        df.to_csv(filename, index=False)

                        # Hiển thị popup và tạm dừng camera
                        st.session_state["scanned_student"] = new_row
                        st.session_state["is_scanning"] = False
                        cap.release()
                        if "user" in st.session_state:
                            st.session_state["keep_user"] = st.session_state["user"]

                        st.rerun()
                time.sleep(0.3)

            stframe.image(frame, channels="BGR")

    else:
        st.session_state["is_scanning"] = False

    # Hiển thị danh sách điểm danh
    st.divider()
    st.markdown("### 🧾 Danh sách học sinh đã điểm danh hôm nay")
    st.dataframe(df, use_container_width=True)

    
    

# ===================== THỐNG KÊ =====================
def view_statistics(user, admin_view_all=False):
    st.subheader("📅 Thống kê điểm danh")

    # Lấy danh sách file điểm danh
    files = [f for f in os.listdir() if f.startswith("attendance_") and f.endswith(".csv")]
    if not files:
        st.info("Chưa có dữ liệu.")
        return

    username = slugify(user["username"])

    # Nếu là admin hoặc superadmin: xem tất cả file
    if admin_view_all:
        selected_file = st.selectbox("📂 Chọn file", files)
    else:
        # Lọc file có tên giáo viên trong đó
        files = [f for f in files if f"_{username}_" in f]
        if not files:
            st.info("Không có dữ liệu cho bạn.")
            return
        selected_file = st.selectbox("📂 Chọn file", files)

    # Đọc dữ liệu file được chọn
    df = pd.read_csv(selected_file)
    if df.empty:
        st.warning("⚠️ File này chưa có bản ghi điểm danh.")
        return

    # Tự động nhận cột thời gian
    time_col = "timestamp" if "timestamp" in df.columns else (
        "Thời gian" if "Thời gian" in df.columns else None
    )
    if time_col is None:
        st.error("❌ Không tìm thấy cột thời gian (timestamp / Thời gian).")
        return

    # Hiển thị tổng quan
    c1, c2 = st.columns(2)
    with c1:
        st.metric("👨‍🎓 Tổng lượt điểm danh", len(df))
    with c2:
        st.metric("📅 Số ngày học", df[time_col].astype(str).str[:10].nunique())

    # Bộ lọc ngày
    selected_day = st.date_input("📆 Chọn ngày", datetime.now().date())
    selected_day_str = selected_day.strftime("%Y-%m-%d")

    filtered = df[df[time_col].astype(str).str.contains(selected_day_str, na=False)]

    if len(filtered):
        st.success(f"📋 Danh sách điểm danh ngày {selected_day_str}:")
        st.dataframe(filtered, use_container_width=True)
    else:
        st.warning("Không có dữ liệu ngày này.")

    # Nút tải CSV
    with open(selected_file, "rb") as f:
        st.download_button("📥 Tải CSV", f, file_name=selected_file)

# ===================== CHẠY ỨNG DỤNG =====================


# ===================== CHẠY ỨNG DỤNG =====================
# 🔄 Tự đăng nhập lại nếu có ghi nhớ
ensure_csv_files()
auto_login()
if "keep_user" in st.session_state:
    st.session_state["user"] = st.session_state["keep_user"]
    del st.session_state["keep_user"]
# ✅ Sau khi auto đăng nhập, hiển thị giao diện phù hợp
if not is_logged_in():
    login_view()
else:
    main_menu()


