#streamlit hello
#streamlit run your_app.py
#pip install streamlit pandas pathlib

import streamlit as st
#이미지 추가
# from streamlit.components.v1 import html #사용자 정의 컴포넌트
# import streamlit.components.v1 as components
# import React, { useState } from 'react';
# import { Button } from '@/components/ui/button';
# import {
#   Dialog,
#   DialogContent,
#   DialogHeader,
#   DialogTitle,
#   DialogTrigger,
# } from '@/components/ui/dialog';

from PIL import Image
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib
import uuid
from pathlib import Path
import os

# Streamlit 애플리케이션 설정

#설정 및 페이지 구성
st.set_page_config(
    page_title="퓨처 리걸 허브, 랫치위 갤러리",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
    )

#CSS 스타일 추가
st.markdown("""
        <style>
        #로고 이미지 컨테이너 스타일
        .logo-container {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem 0;
        }
        
        #로고 이미지 스타일
        .logo-img {
            max-width: 200px; #원하는 크기
            height: auto;
            transition: transform 0.3s ease; #애니메이션 추가1
        }
        
        #애니메이션 추가2
        .logo-img:hover {
            transform: scale(1.1);
        }
        
        #다크/라이트모드 대응
        @media (prefers-color-sheme: light) {
            .main-title {
                color: #000000;
            }
        }
        
        #제목 스타일
        .main-title {
            font-size: 2.5rem;
            font-weight: bold;
            color: #ffffff;
            text-align: center;
            padding: 1rem 0;
        }
        
        #카드 스타일
        .stExpander {
            background-color: #19191a;
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        #버튼 스타일
        .stButton>button {
            background-color: #1cff00;
            color: #000000;
            border: none;
            border-radius: 5px;
            padding: 0.5rem 1rem;
            font-weight: bold;
        }
        
        #사이드바 스타일
        .css-1d391kg {
            background-color: #19191a;
        }
    </style>
""", unsafe_allow_html=True)

#로고 및 제목 표시
def display_logo_and_title():
    logo_path = os.path.join("assets", "logo.png")
    
    try:
        logo = Image.open(logo_path)
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
                        <div class = "logo-container">
                            <img src = "data:image/png;base64,{}" class = "logo-img">
                        </div>
                    """.format(get_image_base64(logo_path)), unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("로고 파일을 찾을 수 없습니다. assets 폴더에 logo.png 파일이 있는지 확인해주세요.")
        
    st.markdown('<h1 class="main-title">퓨처 리걸 허브, 랫치위 갤러리입니다.🌿</h1>', unsafe_allow_html=True)
                
#이미지를 base64로 변환하는 함수
def get_image_base64(image_path):
    import base64
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect('legal_prompts.db')
    c = conn.cursor()
    
    # 사용자 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id TEXT PRIMARY KEY,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  role TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # 프롬프트 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS prompts
                 (id TEXT PRIMARY KEY,
                  title TEXT NOT NULL,
                  content TEXT NOT NULL,
                  category TEXT NOT NULL,
                  author_id TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (author_id) REFERENCES users(id))''')
    
    # 평가 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS ratings
                 (id TEXT PRIMARY KEY,
                  prompt_id TEXT NOT NULL,
                  user_id TEXT NOT NULL,
                  rating INTEGER NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (prompt_id) REFERENCES prompts(id),
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # 좋아요 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS likes
                 (id TEXT PRIMARY KEY,
                  prompt_id TEXT NOT NULL,
                  user_id TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (prompt_id) REFERENCES prompts(id),
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # 댓글 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS comments
                 (id TEXT PRIMARY KEY,
                  prompt_id TEXT NOT NULL,
                  user_id TEXT NOT NULL,
                  content TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (prompt_id) REFERENCES prompts(id),
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

# 비밀번호 해시 함수
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 사용자 인증
def authenticate_user(username, password):
    conn = sqlite3.connect('legal_prompts.db')
    c = conn.cursor()
    c.execute('SELECT id, username, role FROM users WHERE username = ? AND password = ?',
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

# 새 사용자 등록
def register_user(username, password, email, role='user'):
    conn = sqlite3.connect('legal_prompts.db')
    c = conn.cursor()
    try:
        user_id = str(uuid.uuid4())
        c.execute('INSERT INTO users (id, username, password, email, role) VALUES (?, ?, ?, ?, ?)',
                 (user_id, username, hash_password(password), email, role))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

# 프롬프트 저장
def save_prompt(title, content, category, author_id):
    conn = sqlite3.connect('legal_prompts.db')
    c = conn.cursor()
    prompt_id = str(uuid.uuid4())
    c.execute('''INSERT INTO prompts (id, title, content, category, author_id)
                 VALUES (?, ?, ?, ?, ?)''',
              (prompt_id, title, content, category, author_id))
    conn.commit()
    conn.close()
    return prompt_id

# 프롬프트 수정
def update_prompt(prompt_id, title, content, category):
    conn = sqlite3.connect('legal_prompts.db')
    c = conn.cursor()
    c.execute('''UPDATE prompts 
                 SET title = ?, content = ?, category = ?, updated_at = CURRENT_TIMESTAMP
                 WHERE id = ?''',
              (title, content, category, prompt_id))
    conn.commit()
    conn.close()

# 프롬프트 삭제
def delete_prompt(prompt_id):
    conn = sqlite3.connect('legal_prompts.db')
    c = conn.cursor()
    c.execute('DELETE FROM prompts WHERE id = ?', (prompt_id,))
    conn.commit()
    conn.close()

# 평가 추가/수정
def rate_prompt(prompt_id, user_id, rating):
    conn = sqlite3.connect('legal_prompts.db')
    c = conn.cursor()
    c.execute('SELECT id FROM ratings WHERE prompt_id = ? AND user_id = ?',
              (prompt_id, user_id))
    existing_rating = c.fetchone()
    
    if existing_rating:
        c.execute('UPDATE ratings SET rating = ? WHERE prompt_id = ? AND user_id = ?',
                 (rating, prompt_id, user_id))
    else:
        rating_id = str(uuid.uuid4())
        c.execute('INSERT INTO ratings (id, prompt_id, user_id, rating) VALUES (?, ?, ?, ?)',
                 (rating_id, prompt_id, user_id, rating))
    
    conn.commit()
    conn.close()

# 댓글 추가
def add_comment(prompt_id, user_id, content):
    conn = sqlite3.connect('legal_prompts.db')
    c = conn.cursor()
    comment_id = str(uuid.uuid4())
    c.execute('INSERT INTO comments (id, prompt_id, user_id, content) VALUES (?, ?, ?, ?)',
              (comment_id, prompt_id, user_id, content))
    conn.commit()
    conn.close()

# 데이터베이스 초기화
init_db()

# 세션 상태 초기화
if 'user' not in st.session_state:
    st.session_state.user = None

# 사이드바 - 로그인/회원가입
with st.sidebar:
    st.title("사용자 인증")
    if st.session_state.user is None:
        tab1, tab2 = st.tabs(["로그인", "회원가입"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("사용자명")
                password = st.text_input("비밀번호", type="password")
                submit = st.form_submit_button("로그인")
                
                if submit:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.user = {
                            'id': user[0],
                            'username': user[1],
                            'role': user[2]
                        }
                        st.success("기여자님, 반가워요.")
                        st.rerun()
                    else:
                        st.error("로그인에 실패했어요.")
        
        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("사용자명")
                new_email = st.text_input("이메일")
                new_password = st.text_input("비밀번호", type="password")
                confirm_password = st.text_input("비밀번호 확인", type="password")
                submit = st.form_submit_button("회원가입")
                
                if submit:
                    if new_password != confirm_password:
                        st.error("비밀번호가 일치하지 않아요.")
                    else:
                        if register_user(new_username, new_password, new_email):
                            st.success("새로운 기여자님, 로그인해주세요.")
                        else:
                            st.error("이미 존재하는 기여자명 또는 이메일이에요.")
    else:
        st.write(f"반가워요. {st.session_state.user['username']}님!")
        if st.button("로그아웃"):
            st.session_state.user = None
            st.rerun()

# 메인 페이지
st.title("퓨처 리걸 허브, 랫치위 갤러리입니다.🌿")

# st.image("sunrise.jpg", caption="Sunrise by the mountains")

# 페이지 하단 스타일링 및 가이드라인
# st.markdown("---")
st.markdown("### 기여자를 위한 가이드라인")
#버튼 클릭으로 표시되는 가이드라인
if st.button("효과적인 프롬프트 작성을 위한 원칙 10가지"):
    with st.container():
        st.markdown("""
            업데이트를 기대해주세요!
        """)   
    # with st.container():
    #     st.markdown("""
    #     <div style='line-height: 2.5;'>
    # 0️⃣ AI에게 AI 활용법을 질문합니다.
    
    # 1️⃣ AI에게 구체적인 맥락을 제공합니다.
    
    # 2️⃣ AI에게 단계별로 분석하도록 요청합니다.
    
    # 3️⃣ AI에게 특정 관점을 지정하거나 역할을 부여합니다.
    
    # 4️⃣ AI에게 필요하다면 가이드라인을 줍니다.
    
    # 5️⃣ AI에게 사례를 기반으로 학습시킵니다.
    
    # 6️⃣ AI에게 인용시에는 구체적인 판례 번호 등을 요청합니다.
    
    # 7️⃣ AI에게 복잡한 법률 문제는 하위 질문으로 나눠
    #    단계적으로 접근하라고 요청합니다.
    
    # 8️⃣ AI에게 가상 시나리오를 제공하여 맥락을 이해시킵니다.
    
    # 9️⃣ AI에게 원하는 답변의 형식이나 길이를 지정합니다.
    
    # 🔟 AI 활용에만 집중하지 말고 최대 효율에 집중해
    #    원하는 결과를 얻어보세요.
    # </div>
    # """, unsafe_allow_html=True)
                        
        if st.button("닫기"):
            st.rerun()        

# """)
# st.markdown("""
# - 명확하고 구체적인 지시사항을 포함해주세요
# - 예시와 함께 작성하면 더 효과적입니다
# - 개인정보가 포함되지 않도록 주의해주세요
# - 법률 용어를 정확하게 사용해주세요
# - 필요한 경우 참고 법령을 함께 기재해주세요
# """)

# 카테고리 필터
categories = ["전체", "1. 법률 AI", "2. 법률 문서 자동화", "3. 법률 데이터 분석", "4. 법무 업무 자동화", "5. 컴플라이언스", "6. 법률 리서치", "기타"]
selected_category = st.selectbox("카테고리를 선택해요.", categories)

# 검색 기능
search_term = st.text_input("허브에서 무엇을 찾으시나요?")

# 탭 생성
if st.session_state.user:
    tab1, tab2 = st.tabs(["허브 탐색하기", "허브에 새로운 기여 남기기"])
else:
    tab1, tab2 = st.tabs(["허브 탐색하기", "로그인이 필요해요."])

# 프롬프트 목록 표시
with tab1:
    conn = sqlite3.connect('legal_prompts.db')
    prompts_df = pd.read_sql_query('''
        SELECT p.*, u.username as author_name,
               (SELECT COUNT(*) FROM likes WHERE prompt_id = p.id) as like_count,
               (SELECT AVG(rating) FROM ratings WHERE prompt_id = p.id) as avg_rating,
               (SELECT COUNT(*) FROM ratings WHERE prompt_id = p.id) as rating_count
        FROM prompts p
        JOIN users u ON p.author_id = u.id
        WHERE (? = '전체' OR p.category = ?)
        AND (p.title LIKE ? OR p.content LIKE ?)
        ORDER BY p.created_at DESC
    ''', conn, params=(selected_category, selected_category,
                      f'%{search_term}%', f'%{search_term}%'))
    
    for _, prompt in prompts_df.iterrows():
        with st.expander(f"{prompt['title']} - {prompt['author_name']}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**카테고리:** {prompt['category']}")
                st.write(f"**작성일:** {prompt['created_at']}")
                st.text_area("내용", prompt['content'], height=100,
                           key=f"content_{prompt['id']}", disabled=True)
                
                # 프롬프트 수정/삭제 (작성자 또는 관리자만)
                if st.session_state.user and \
                   (st.session_state.user['id'] == prompt['author_id'] or 
                    st.session_state.user['role'] == 'admin'):
                    if st.button("수정", key=f"edit_{prompt['id']}"):
                        st.session_state.editing = prompt['id']
                    if st.button("삭제", key=f"delete_{prompt['id']}"):
                        delete_prompt(prompt['id'])
                        st.success("작성글이 삭제됐어요.")
                        st.rerun()
            
            with col2:
                # 평점 표시
                avg_rating = prompt['avg_rating'] or 0
                st.write(f"평균 평점: {'%.1f' % avg_rating} ⭐ ({int(prompt['rating_count'])}개 평가)")
                
                # 로그인한 사용자만 평가 가능
                if st.session_state.user:
                    new_rating = st.select_slider(
                        "평점",
                        options=[1, 2, 3, 4, 5],
                        key=f"rating_{prompt['id']}"
                    )
                    if st.button("평점 남기기", key=f"submit_rating_{prompt['id']}"):
                        rate_prompt(prompt['id'], st.session_state.user['id'], new_rating)
                        st.success("평점을 남겼어요.")
                        st.rerun()
                
                # 좋아요 수 표시
                st.write(f"좋아요: {int(prompt['like_count'])} 👍")
            
            # 댓글 섹션
            st.markdown("---")
            st.subheader("댓글")
            
            # 댓글 표시
            comments_df = pd.read_sql_query('''
                SELECT c.*, u.username
                FROM comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.prompt_id = ?
                ORDER BY c.created_at DESC
            ''', conn, params=(prompt['id'],))
            
            for _, comment in comments_df.iterrows():
                st.write(f"**{comment['username']}:** {comment['content']}")
                st.write(f"*{comment['created_at']}*")
                st.markdown("---")
            
            # 로그인한 사용자만 댓글 작성 가능
            if st.session_state.user:
                with st.form(key=f"comment_form_{prompt['id']}"):
                    comment_content = st.text_area("댓글 작성")
                    submit_comment = st.form_submit_button("댓글 등록")
                    
                    if submit_comment and comment_content:
                        add_comment(prompt['id'], st.session_state.user['id'], comment_content)
                        st.success("댓글이 등록되었습니다!")
                        st.rerun()
    
    conn.close()

# 새 프롬프트 작성 (이전 코드에서 이어짐)
with tab2:
    if st.session_state.user:
        with st.form("new_prompt_form"):
            title = st.text_input("제목")
            content = st.text_area("내용", height=200)
            category = st.selectbox("카테고리", categories[1:])  # "전체" 제외
            
            submitted = st.form_submit_button("기여")
            if submitted:
                if title and content and category:
                    save_prompt(title, content, category, st.session_state.user['id'])
                    st.success("새로운 기여활동에 감사해요.")
                    st.rerun()
                else:
                    st.error("모든 필드를 입력해주세요.")
    else:
        st.warning("새로운 기여는 로그인이 필요해요.")

# 프롬프트 수정 모달 (세션 상태에 editing이 있을 때 표시)
if st.session_state.get('editing'):
    st.subheader("수정")
    conn = sqlite3.connect('legal_prompts.db')
    c = conn.cursor()
    c.execute('SELECT * FROM prompts WHERE id = ?', (st.session_state.editing,))
    prompt = c.fetchone()
    conn.close()

    if prompt:
        with st.form("edit_prompt_form"):
            edited_title = st.text_input("제목", value=prompt[1])
            edited_content = st.text_area("내용", value=prompt[2], height=200)
            edited_category = st.selectbox("카테고리", categories[1:], 
                                         index=categories[1:].index(prompt[3]))
            
            col1, col2 = st.columns(2)
            with col1:
                submit_edit = st.form_submit_button("수정 완료")
            with col2:
                cancel_edit = st.form_submit_button("취소")
            
            if submit_edit:
                if edited_title and edited_content and edited_category:
                    update_prompt(st.session_state.editing, edited_title, 
                                edited_content, edited_category)
                    del st.session_state.editing
                    st.success("수정되었습니다!")
                    st.rerun()
                else:
                    st.error("모든 필드를 입력해주세요.")
            
            if cancel_edit:
                del st.session_state.editing
                st.rerun()


# 관리자 전용 섹션
if st.session_state.user and st.session_state.user['role'] == 'admin':
    st.markdown("---")
    st.subheader("🔧 관리자 도구")
    
    # 사용자 관리
    if st.checkbox("사용자 관리"):
        conn = sqlite3.connect('legal_prompts.db')
        users_df = pd.read_sql_query('''
            SELECT id, username, email, role, created_at
            FROM users
            ORDER BY created_at DESC
        ''', conn)
        conn.close()
        
        st.dataframe(users_df)
    
    # 통계
    if st.checkbox("통계 보기"):
        conn = sqlite3.connect('legal_prompts.db')
        c = conn.cursor()
        
        # 총 프롬프트 수
        c.execute('SELECT COUNT(*) FROM prompts')
        total_prompts = c.fetchone()[0]
        
        # 총 사용자 수
        c.execute('SELECT COUNT(*) FROM users')
        total_users = c.fetchone()[0]
        
        # 카테고리별 프롬프트 수
        category_stats = pd.read_sql_query('''
            SELECT category, COUNT(*) as count
            FROM prompts
            GROUP BY category
        ''', conn)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("총 프롬프트 수", total_prompts)
            st.metric("총 사용자 수", total_users)
        
        with col2:
            st.write("카테고리별 프롬프트 수")
            st.dataframe(category_stats)
        
        conn.close()

# 에러 처리 및 데이터베이스 연결 관리
def handle_error(error):
    st.error(f"오류가 발생했습니다: {str(error)}")
    if 'conn' in locals():
        conn.close()

try:
    # 데이터베이스 백업 (매일 자정에 실행되도록 설정 필요)
    def backup_database():
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        backup_file = backup_dir / f"legal_prompts_backup_{datetime.now().strftime('%Y%m%d')}.db"
        os.system(f"sqlite3 legal_prompts.db '.backup {backup_file}'")

except Exception as e:
    handle_error(e)
