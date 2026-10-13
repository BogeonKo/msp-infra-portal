import streamlit as st
import os
import subprocess

st.set_page_config(page_title="MSP 인프라 배포 포털", layout="wide")

# ==========================================
# 세션 상태 초기화
# ==========================================
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'customer_dir' not in st.session_state:
    st.session_state.customer_dir = ""
if 'plan_output' not in st.session_state:
    st.session_state.plan_output = ""

if 'vpc_ids' not in st.session_state:
    st.session_state.vpc_ids = [0]
    st.session_state.subnet_ids = {0: [0]} 
    st.session_state.next_vpc_id = 1
    st.session_state.next_subnet_id = 1

def add_vpc():
    vid = st.session_state.next_vpc_id
    st.session_state.vpc_ids.append(vid)
    st.session_state.subnet_ids[vid] = [st.session_state.next_subnet_id]
    st.session_state.next_vpc_id += 1
    st.session_state.next_subnet_id += 1

def delete_vpc(vid):
    st.session_state.vpc_ids.remove(vid)
    if vid in st.session_state.subnet_ids:
        del st.session_state.subnet_ids[vid]

def add_subnet(vid):
    sid = st.session_state.next_subnet_id
    st.session_state.subnet_ids[vid].append(sid)
    st.session_state.next_subnet_id += 1

def delete_subnet(vid, sid):
    st.session_state.subnet_ids[vid].remove(sid)

# --- [사이드바] 인증 정보 ---
st.sidebar.header("🔑 인증 정보")
ncloud_access_key = st.sidebar.text_input("NCP Access Key", type="password")
ncloud_secret_key = st.sidebar.text_input("NCP Secret Key", type="password")

def get_env():
    custom_env = os.environ.copy()
    custom_env["NCLOUD_ACCESS_KEY"] = ncloud_access_key
    custom_env["NCLOUD_SECRET_KEY"] = ncloud_secret_key
    return custom_env

st.title("☁️ MSP 자동화 포털 (NAT GW 포함)")

# ==========================================
# Step 1. 인프라 정보 입력
# ==========================================
st.header("Step 1. 인프라 정보 입력")
customer_name = st.text_input("🏢 고객사 영문명 (예: bgko)", value="bgko")

for v_idx, vid in enumerate(st.session_state.vpc_ids):
    with st.expander(f"🌐 VPC {v_idx + 1} 설정 영역", expanded=True):
        
        vc1, vc2, vc3 = st.columns([2, 2, 1])
        with vc1:
            st.text_input(f"VPC {v_idx+1} 접미사", value=f"vpc-{v_idx+1}", key=f"vpc_suffix_{vid}")
        with vc2:
            st.text_input(f"VPC {v_idx+1} IP 대역 (CIDR)", value=f"10.{v_idx}.0.0/16", key=f"vpc_cidr_{vid}")
        with vc3:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if len(st.session_state.vpc_ids) > 1:
                st.button(f"🗑️ VPC 삭제", key=f"del_vpc_{vid}", on_click=delete_vpc, args=(vid,), type="primary", use_container_width=True)
        
# ★ [수정됨] NAT Gateway 설정 영역
        st.markdown("---")
        st.markdown("**🌍 NAT Gateway 설정 (외부 통신용)**")
        nc1, nc2, nc3 = st.columns([1, 1.5, 1.5])
        with nc1:
            nat_checked = st.checkbox("NAT GW 생성하기", value=False, key=f"nat_create_{vid}")
        
        if nat_checked:
            with nc2:
                # NAT GW 이름 입력칸 활성화
                st.text_input("NAT GW 이름", value=f"natgw-{v_idx+1}", key=f"nat_name_{vid}")
            with nc3:
                # 현재 화면에 열려있는 서브넷 개수만큼 동적으로 선택지(Subnet 1, Subnet 2...) 생성
                subnet_options = [f"Subnet {i+1}" for i in range(len(st.session_state.subnet_ids[vid]))]
                st.selectbox("연결할 Subnet (NATGW 용도 권장)", subnet_options, key=f"nat_subnet_{vid}")
        else:
            with nc2:
                st.caption("※ Private 서브넷의 아웃바운드 통신이 필요할 경우 체크하세요.")

        st.markdown("---")
        st.markdown("**🔀 이 VPC에 속한 Subnet 목록**")
        
        for s_idx, sid in enumerate(st.session_state.subnet_ids[vid]):
            sc1, sc2, sc3, sc4, sc5, sc6 = st.columns([1.3, 1, 0.8, 1.2, 0.7, 0.4])
            with sc1:
                st.text_input(f"Subnet {s_idx+1} 접미사", key=f"sub_suffix_{vid}_{sid}", placeholder="미입력시 자동생성")
            with sc2:
                st.selectbox(f"용도", ["일반 (GEN)", "로드밸런서 (LOADB)", "NAT GW (NATGW)", "베어메탈 (BM)"], key=f"sub_usage_{vid}_{sid}")
            with sc3:
                st.selectbox(f"타입", ["PUBLIC", "PRIVATE"], key=f"sub_type_{vid}_{sid}")
            with sc4:
                st.text_input(f"IP 대역", value=f"10.{v_idx}.{s_idx}.0/24", key=f"sub_cidr_{vid}_{sid}")
            with sc5:
                st.selectbox(f"가용존", ["KR-1", "KR-2"], key=f"sub_zone_{vid}_{sid}")
            with sc6:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                if len(st.session_state.subnet_ids[vid]) > 1:
                    st.button("❌", key=f"del_sub_{vid}_{sid}", on_click=delete_subnet, args=(vid, sid), help="서브넷 삭제", use_container_width=True)
                    
        st.button(f"➕ Subnet 추가 (VPC {v_idx+1})", key=f"add_sub_{vid}", on_click=add_subnet, args=(vid,))

st.button("➕ 새로운 VPC 환경 추가", on_click=add_vpc)
st.divider()

# ==========================================
# 테라폼 파일 자동 생성 및 Init 로직
# ==========================================
if st.button("⚙️ 위 설정으로 파일 생성 및 초기화 (Init)", type="primary"):
    if not ncloud_access_key or not ncloud_secret_key:
        st.error("좌측 사이드바에 API Key와 Secret Key를 모두 입력해주세요.")
    elif not customer_name.strip():
        st.error("고객사 이름을 입력해주세요.")
    else:
        customer_dir = customer_name.strip()
        st.session_state.customer_dir = customer_dir
        os.makedirs(customer_dir, exist_ok=True)
        
        main_tf_content = """terraform {
  required_providers { ncloud = { source = "NaverCloudPlatform/ncloud" } }
}
provider "ncloud" { 
  region      = "KR" 
  support_vpc = true
}
"""
        for v_idx, vid in enumerate(st.session_state.vpc_ids):
            v_suffix = st.session_state[f"vpc_suffix_{vid}"].strip()
            v_cidr = st.session_state[f"vpc_cidr_{vid}"].strip()
            vpc_resource_id = f"vpc_{vid}"
            
            main_tf_content += f"""
# ==========================================
# VPC {v_idx + 1} 생성
# ==========================================
resource "ncloud_vpc" "{vpc_resource_id}" {{
  name            = "{customer_dir}-{v_suffix}"
  ipv4_cidr_block = "{v_cidr}"
}}
"""
            # ★ [수정됨] NAT Gateway 테라폼 코드 동적 생성
            if st.session_state.get(f"nat_create_{vid}", False):
                nat_name = st.session_state[f"nat_name_{vid}"].strip()
                nat_subnet_str = st.session_state[f"nat_subnet_{vid}"] # 예: "Subnet 1"
                
                # "Subnet 1"이라는 텍스트에서 인덱스(0)를 추출하여 실제 Subnet 고유 ID와 매핑
                selected_sub_idx = int(nat_subnet_str.split(" ")[1]) - 1
                selected_sid = st.session_state.subnet_ids[vid][selected_sub_idx]
                selected_sub_resource_id = f"sub_{vid}_{selected_sid}"
                
                nat_resource_id = f"nat_{vid}"
                
                # NAT GW는 선택된 Subnet의 Zone 정보까지 자동으로 쏙 빼와서(Inherit) 사용합니다.
                main_tf_content += f"""
# ==========================================
# NAT Gateway 생성 (VPC {v_idx + 1})
# ==========================================
resource "ncloud_nat_gateway" "{nat_resource_id}" {{
  vpc_no    = ncloud_vpc.{vpc_resource_id}.vpc_no
  subnet_no = ncloud_subnet.{selected_sub_resource_id}.subnet_no
  zone      = ncloud_subnet.{selected_sub_resource_id}.zone
  name      = "{customer_dir}-{nat_name}"
}}
"""
            for s_idx, sid in enumerate(st.session_state.subnet_ids[vid]):
                s_suffix_input = st.session_state[f"sub_suffix_{vid}_{sid}"].strip()
                s_usage_raw = st.session_state[f"sub_usage_{vid}_{sid}"]
                s_type = st.session_state[f"sub_type_{vid}_{sid}"]
                s_cidr = st.session_state[f"sub_cidr_{vid}_{sid}"].strip()
                s_zone = st.session_state[f"sub_zone_{vid}_{sid}"]
                
                if "LOADB" in s_usage_raw:
                    s_usage = "LOADB"
                elif "NATGW" in s_usage_raw:
                    s_usage = "NATGW"
                elif "BM" in s_usage_raw:
                    s_usage = "BM"
                else:
                    s_usage = "GEN"
                
                if s_suffix_input:
                    sub_name = f"{customer_dir}-{s_suffix_input}"
                else:
                    sub_name = f"{customer_dir}-{s_type.lower()}-{s_usage.lower()}-sub{s_idx+1}"
                
                sub_resource_id = f"sub_{vid}_{sid}"
                
                main_tf_content += f"""
resource "ncloud_subnet" "{sub_resource_id}" {{
  vpc_no         = ncloud_vpc.{vpc_resource_id}.vpc_no
  subnet         = "{s_cidr}"
  zone           = "{s_zone}"
  network_acl_no = ncloud_vpc.{vpc_resource_id}.default_network_acl_no
  subnet_type    = "{s_type}"
  name           = "{sub_name}"
  usage_type     = "{s_usage}"
}}
"""
        # 1. 파일 생성 (기존 로직)
        with open(os.path.join(customer_dir, "main.tf"), "w", encoding="utf-8") as f:
            f.write(main_tf_content)
            
        # ==========================================
        # ★ [수정됨] Git 타겟 지정 커밋 & 푸시 로직
        # ==========================================
        with st.spinner("GitHub에 인프라 구성 코드를 백업하는 중..."):
            try:
                # 변경 전: subprocess.run(["git", "add", "."], ...) 
                # 변경 후: 방금 만든 고객사 폴더(customer_dir)만 지정해서 깃허브에 올릴 준비를 함
                subprocess.run(["git", "add", customer_dir], check=True, capture_output=True)
                
                commit_msg = f"Auto-generated: {customer_dir} 인프라 뼈대 구성 (VPC, Subnet, NAT)"
                subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
                
                subprocess.run(["git", "push"], check=True, capture_output=True)
                
                st.success(f"🐙 GitHub에 [{customer_dir}] 코드 백업 완료!")
            except subprocess.CalledProcessError:
                st.info("Git 변경사항이 없거나 Push에 실패했습니다.")
        # ==========================================

        # 이후 기존의 Terraform Init 및 Apply 로직 계속 진행...
            
        with st.spinner("Terraform Init 진행 중..."):
            init_result = subprocess.run(["terraform", "init"], cwd=customer_dir, env=get_env(), capture_output=True, text=True, encoding="utf-8")
            if init_result.returncode == 0:
                st.success(f"✅ [{customer_dir}] 폴더 생성 및 코드 작성 완료!")
                st.session_state.step = 2 
            else:
                st.error("🚨 Init 실패")
                st.code(init_result.stderr)

# ==========================================
# Step 2 & 3 (이전과 동일)
# ==========================================
if st.session_state.step >= 2:
    st.divider()
    st.header("Step 2. 인프라 검사 (Plan)")
    if st.button("검사 및 계획(Plan) 실행"):
        with st.spinner("배포 계획 생성 중..."):
            val_result = subprocess.run(["terraform", "validate"], cwd=st.session_state.customer_dir, capture_output=True, text=True, encoding="utf-8")
            if val_result.returncode != 0:
                st.error("🚨 문법 오류")
                st.code(val_result.stderr)
            else:
                plan_result = subprocess.run(["terraform", "plan", "-no-color"], cwd=st.session_state.customer_dir, env=get_env(), capture_output=True, text=True, encoding="utf-8")
                if plan_result.returncode == 0:
                    st.session_state.plan_output = plan_result.stdout
                    st.session_state.step = 3 
                    st.success("✅ 검증 완료!")
                else:
                    st.error("🚨 Plan 실패")
                    st.code(plan_result.stderr)
                    
    if st.session_state.plan_output:
        with st.expander("🔍 리소스 목록 확인", expanded=True):
            st.code(st.session_state.plan_output, language="text")

if st.session_state.step >= 3:
    st.divider()
    st.header("Step 3. 최종 배포 (Apply)")
    if st.button("🚀 배포 실행 (Apply)", type="primary"):
        with st.spinner("인프라 생성 중... (NAT GW는 시간이 조금 더 소요될 수 있습니다)"):
            apply_result = subprocess.run(["terraform", "apply", "-auto-approve", "-no-color"], cwd=st.session_state.customer_dir, env=get_env(), capture_output=True, text=True, encoding="utf-8")
            if apply_result.returncode == 0:
                st.success("🎉 배포 성공!")
                with st.expander("로그 확인"):
                    st.code(apply_result.stdout)
            else:
                st.error("🚨 오류 발생")
                st.code(apply_result.stderr)