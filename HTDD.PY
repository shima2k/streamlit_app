import streamlit as st
import qrcode
import pandas as pd
from datetime import datetime
import cv2
import tempfile
import os

# -------------------- Cấu hình trang --------------------
st.set_page_config(page_title="Hệ thống điểm danh QR", page_icon="🎓", layout="wide")

st.title("🎓 HỆ THỐNG ĐIỂM DANH HỌC SINH BẰNG MÃ QR")

menu = st.sidebar.radio("📌 Chọn chức năng", ["🏷️ Tạo mã QR", "📸 Điểm danh", "📅 Thống kê"])

# -------------------- 1️⃣ SINH MÃ QR --------------------
if menu == "🏷️ Tạo mã QR":
    st.subheader("📇 Tạo mã QR cho học sinh")
    name = st.text_input("Tên học sinh")
    student_id = st.text_input("Mã học sinh (ví dụ: HS001)")
    classroom = st.text_input("Lớp (ví dụ: 10A1)")

    if st.button("🎁 Tạo mã QR"):
        if name and student_id and classroom:
            data = f"{student_id} - {name} - {classroom}"
            qr = qrcode.make(data)
            os.makedirs("qr_codes", exist_ok=True)
            qr_path = f"qr_codes/{student_id}.png"
            qr.save(qr_path)

            st.image(qr_path, caption=f"Mã QR của {name}", width=250)
            with open(qr_path, "rb") as f:
                st.download_button("⬇️ Tải mã QR", f, file_name=f"{student_id}.png")
            st.success("✅ Đã tạo mã QR thành công!")
        else:
            st.warning("⚠️ Vui lòng nhập đầy đủ thông tin trước khi tạo!")

# -------------------- 2️⃣ ĐIỂM DANH --------------------
elif menu == "📸 Điểm danh":
    st.subheader("📷 Quét mã QR để điểm danh")

    attendance_file = "attendance.csv"
    if not os.path.exists(attendance_file):
        pd.DataFrame(columns=["ID", "Tên học sinh", "Lớp", "Thời gian"]).to_csv(attendance_file, index=False)

    run = st.checkbox("Bật camera")
    FRAME_WINDOW = st.image([])

    if run:
        cap = cv2.VideoCapture(0)
        detector = cv2.QRCodeDetector()

        while run:
            ret, frame = cap.read()
            if not ret:
                st.error("Không thể mở camera!")
                break

            data, bbox, _ = detector.detectAndDecode(frame)
            if data:
                try:
                    ID, name, classroom = data.split(" - ")
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    df = pd.read_csv(attendance_file)

                    # Kiểm tra xem học sinh đã điểm danh hôm nay chưa
                    today = datetime.now().strftime("%Y-%m-%d")
                    already = ((df["ID"] == ID) & (df["Thời gian"].str.contains(today))).any()

                    if not already:
                        df.loc[len(df)] = [ID, name, classroom, timestamp]
                        df.to_csv(attendance_file, index=False)
                        st.success(f"✅ {name} ({classroom}) đã điểm danh lúc {timestamp}")
                    else:
                        st.info(f"⚠️ {name} đã điểm danh hôm nay.")
                except Exception as e:
                    st.error(f"❌ Lỗi khi đọc mã QR: {e}")

            FRAME_WINDOW.image(frame, channels="BGR")

            # 🆕 Bảng danh sách học sinh điểm danh hôm nay (tự cập nhật)
            with st.expander("📋 Danh sách học sinh đã điểm danh hôm nay", expanded=True):
                df = pd.read_csv(attendance_file)
                today_df = df[df["Thời gian"].str.contains(datetime.now().strftime("%Y-%m-%d"))]
                st.dataframe(today_df.sort_values(by="Thời gian", ascending=False))

        cap.release()

    else:
        # Nếu camera tắt vẫn hiện danh sách cũ
        if os.path.exists(attendance_file):
            st.write("📋 Danh sách học sinh đã điểm danh hôm nay:")
            df = pd.read_csv(attendance_file)
            today_df = df[df["Thời gian"].str.contains(datetime.now().strftime("%Y-%m-%d"))]
            st.dataframe(today_df.sort_values(by="Thời gian", ascending=False))
        else:
            st.info("Chưa có dữ liệu điểm danh nào.")

# -------------------- 3️⃣ THỐNG KÊ --------------------
elif menu == "📅 Thống kê":
    st.subheader("📊 Thống kê điểm danh")
    if os.path.exists("attendance.csv"):
        df = pd.read_csv("attendance.csv")
        df["Ngày"] = df["Thời gian"].str[:10]

        col1, col2 = st.columns(2)
        with col1:
            st.metric("👨‍🎓 Tổng số lượt điểm danh", len(df))
        with col2:
            st.metric("📅 Số ngày có điểm danh", df["Ngày"].nunique())

        selected_day = st.date_input("Chọn ngày để xem chi tiết", datetime.now().date())
        selected_day_str = selected_day.strftime("%Y-%m-%d")
        filtered = df[df["Thời gian"].str.contains(selected_day_str)]

        if len(filtered) > 0:
            st.success(f"📋 Danh sách học sinh đã điểm danh ngày {selected_day_str}:")
            st.dataframe(filtered)
        else:
            st.warning(f"Không có dữ liệu điểm danh cho ngày {selected_day_str}.")

        st.download_button("📥 Tải toàn bộ dữ liệu điểm danh", open("attendance.csv", "rb"), file_name="attendance.csv")

    else:
        st.info("❗ Chưa có dữ liệu điểm danh nào để thống kê.")
