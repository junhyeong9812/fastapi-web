-- docker/mariadb/init.sql
-- 상표등록 리서치 사이트용 MariaDB 초기화 스크립트 (완전한 니스분류 포함)

USE fastapi_db;

-- ==========================================
-- 사용자 테이블 (간소화)
-- ==========================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '사용자명',
    email VARCHAR(100) UNIQUE NOT NULL COMMENT '이메일',
    hashed_password VARCHAR(255) NOT NULL COMMENT '해시된 비밀번호',
    is_active BOOLEAN DEFAULT TRUE COMMENT '활성 상태',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci 
  COMMENT='사용자 정보';

-- ==========================================
-- 니스 분류 메인 카테고리 (1-45류 전체)
-- ==========================================
CREATE TABLE IF NOT EXISTS main_categories (
    id INT PRIMARY KEY COMMENT '니스 분류 번호 (1-45)',
    name VARCHAR(100) NOT NULL COMMENT '분류명',
    description TEXT COMMENT '분류 설명',
    category_type ENUM('GOODS', 'SERVICES') NOT NULL COMMENT '상품/서비스 구분',
    is_active BOOLEAN DEFAULT TRUE COMMENT '활성 상태',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    
    INDEX idx_category_type (category_type),
    INDEX idx_name (name)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci 
  COMMENT='니스 분류 메인 카테고리 (1-45류)';

-- ==========================================
-- 유사군코드 서브 카테고리
-- ==========================================
CREATE TABLE IF NOT EXISTS sub_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL COMMENT '유사군코드 (예: G0301)',
    name VARCHAR(200) NOT NULL COMMENT '유사군명',
    description TEXT COMMENT '유사군 설명',
    main_category_id INT NOT NULL COMMENT '메인 카테고리 ID',
    is_active BOOLEAN DEFAULT TRUE COMMENT '활성 상태',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    
    FOREIGN KEY (main_category_id) REFERENCES main_categories(id),
    INDEX idx_code (code),
    INDEX idx_main_category_id (main_category_id),
    INDEX idx_name (name)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci 
  COMMENT='유사군코드 서브 카테고리';

-- ==========================================
-- 상표 정보 테이블
-- ==========================================
CREATE TABLE IF NOT EXISTS trademarks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL COMMENT '상표명(한글)',
    product_name_eng VARCHAR(200) COMMENT '상표명(영문)',
    application_number VARCHAR(50) UNIQUE NOT NULL COMMENT '출원번호',
    application_date DATE NOT NULL COMMENT '출원일',
    register_status VARCHAR(20) NOT NULL COMMENT '등록상태',
    publication_number VARCHAR(50) COMMENT '공개번호',
    publication_date DATE COMMENT '공개일',
    registration_number VARCHAR(50) COMMENT '등록번호',
    registration_date DATE COMMENT '등록일',
    registration_pub_number VARCHAR(50) COMMENT '등록공고번호',
    registration_pub_date DATE COMMENT '등록공고일',
    international_reg_date DATE COMMENT '국제등록일',
    international_reg_numbers JSON COMMENT '국제등록번호들',
    priority_claim_num_list JSON COMMENT '우선권 주장번호 목록',
    priority_claim_date_list JSON COMMENT '우선권 주장일 목록',
    vienna_code_list JSON COMMENT '비엔나 분류코드',
    created_by INT COMMENT '등록자 ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_product_name (product_name),
    INDEX idx_application_number (application_number),
    INDEX idx_application_date (application_date),
    INDEX idx_register_status (register_status),
    INDEX idx_registration_date (registration_date),
    FULLTEXT idx_fulltext_search (product_name, product_name_eng)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci 
  COMMENT='상표 정보';

-- ==========================================
-- 상표-메인카테고리 연결 테이블 (중간테이블로 다대다 해결)
-- ==========================================
CREATE TABLE IF NOT EXISTS trademark_main_categories (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    trademark_id BIGINT NOT NULL COMMENT '상표 ID',
    main_category_id INT NOT NULL COMMENT '메인 카테고리 ID (니스분류)',
    priority_order TINYINT DEFAULT 1 COMMENT '우선순위 (1=주분류, 2=부분류)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    created_by INT COMMENT '등록자 ID',
    
    FOREIGN KEY (trademark_id) REFERENCES trademarks(id) ON DELETE CASCADE,
    FOREIGN KEY (main_category_id) REFERENCES main_categories(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE KEY unique_trademark_main_category (trademark_id, main_category_id),
    INDEX idx_trademark_id (trademark_id),
    INDEX idx_main_category_id (main_category_id),
    INDEX idx_priority_order (priority_order)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci 
  COMMENT='상표-메인카테고리 연결 (다대다 해결)';

-- ==========================================
-- 상표-서브카테고리 연결 테이블 (중간테이블로 다대다 해결)
-- ==========================================
CREATE TABLE IF NOT EXISTS trademark_sub_categories (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    trademark_id BIGINT NOT NULL COMMENT '상표 ID',
    sub_category_id INT NOT NULL COMMENT '서브 카테고리 ID (유사군코드)',
    priority_order TINYINT DEFAULT 1 COMMENT '우선순위',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    created_by INT COMMENT '등록자 ID',
    
    FOREIGN KEY (trademark_id) REFERENCES trademarks(id) ON DELETE CASCADE,
    FOREIGN KEY (sub_category_id) REFERENCES sub_categories(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE KEY unique_trademark_sub_category (trademark_id, sub_category_id),
    INDEX idx_trademark_id (trademark_id),
    INDEX idx_sub_category_id (sub_category_id),
    INDEX idx_priority_order (priority_order)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci 
  COMMENT='상표-서브카테고리 연결 (다대다 해결)';

-- ==========================================
-- 테스트 데이터 삽입
-- ==========================================

-- 사용자 테스트 데이터
INSERT INTO users (username, email, hashed_password) VALUES
('admin', 'admin@trademark-research.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4jx8p8OZC2'),
('researcher1', 'researcher1@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4jx8p8OZC2'),
('researcher2', 'researcher2@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4jx8p8OZC2');

-- ==========================================
-- 니스 분류 1-45류 전체 삽입
-- ==========================================

-- 상품 분류 (1-34류)
INSERT INTO main_categories (id, name, description, category_type) VALUES
(1, '화학제품', '공업용, 과학용, 사진용 화학품, 미가공 인조수지, 플라스틱 소재, 소화조성물, 비료', 'GOODS'),
(2, '페인트/니스', '페인트, 니스, 래커, 방청제, 목재보존제, 착색제, 염료, 인쇄용 잉크', 'GOODS'),
(3, '화장품/세제', '비의료용 화장품 및 세면용품, 치약, 향료, 에센셜오일, 세정제', 'GOODS'),
(4, '연료/양초', '공업용 오일 및 그리스, 왁스, 윤활제, 연료, 발광체, 조명용 양초', 'GOODS'),
(5, '약제/의료용품', '약제, 의료용 및 수의과용 제제, 의료용 위생제, 식이요법용 식품', 'GOODS'),
(6, '금속제품', '일반금속 및 그 합금, 금속제 건축재료, 이동식 건축물, 금속제 케이블', 'GOODS'),
(7, '기계/공구', '기계, 공작기계, 전동공구, 모터 및 엔진, 농기구, 자동판매기', 'GOODS'),
(8, '수공구', '수동식 수공구 및 수동기구, 커틀러리, 휴대무기, 면도기', 'GOODS'),
(9, '전자제품/소프트웨어', '과학, 측량, 사진, 영화 기기, 전기기기, 컴퓨터 및 소프트웨어', 'GOODS'),
(10, '의료기기', '외과용, 내과용, 치과용 기계기구, 의지, 의안, 의치, 정형외과용품', 'GOODS'),
(11, '조명/냉난방', '조명, 가열, 냉각, 조리, 건조, 환기, 급수, 위생용 장치 및 설비', 'GOODS'),
(12, '운송기기', '수송기계기구, 육상, 항공, 해상 이동 수송수단', 'GOODS'),
(13, '화기/폭약', '화기, 탄약 및 발사체, 폭약, 폭죽', 'GOODS'),
(14, '귀금속/액세서리', '귀금속 및 그 합금, 보석, 귀석, 반귀석, 시계용구', 'GOODS'),
(15, '악기', '악기, 악보대 및 악기용 받침대, 지휘봉', 'GOODS'),
(16, '종이/인쇄물', '종이 및 판지, 인쇄물, 제본재료, 사진, 문방구 및 사무용품', 'GOODS'),
(17, '고무/플라스틱', '미가공 및 반가공 고무, 제조용 플라스틱 및 수지, 충전 및 절연용 재료', 'GOODS'),
(18, '가죽/가방', '가죽 및 모조가죽, 수하물가방 및 운반용가방, 우산 및 파라솔, 마구', 'GOODS'),
(19, '비금속 건축재료', '건축용 및 구축용 비금속제 건축재료, 아스팔트, 피치, 타르', 'GOODS'),
(20, '가구/목재', '가구, 거울, 액자, 비금속제 컨테이너, 뼈, 뿔, 나전 등의 제품', 'GOODS'),
(21, '주방/생활용품', '가정용 및 주방용 기구 및 용기, 조리기구 및 식기, 빗, 스펀지, 솔', 'GOODS'),
(22, '로프/섬유', '로프 및 노끈, 망, 텐트 및 타폴린, 차양, 돛, 포대, 미가공 섬유', 'GOODS'),
(23, '실', '직물용 실', 'GOODS'),
(24, '직물/침구', '직물 및 직물대용품, 가정용 린넨, 직물제 및 플라스틱제 커튼', 'GOODS'),
(25, '의류/신발/모자', '의류, 신발, 모자', 'GOODS'),
(26, '액세서리/장식품', '레이스, 자수포, 리본, 단추, 핀 및 바늘, 조화, 머리장식품', 'GOODS'),
(27, '바닥재/벽지', '카펫, 융단, 매트, 리놀륨, 기타 바닥깔개용 재료, 비직물제 벽걸이', 'GOODS'),
(28, '게임/완구/스포츠용품', '오락용구, 장난감, 비디오게임장치, 체조 및 스포츠용품', 'GOODS'),
(29, '가공식품', '식육, 생선, 가금 및 엽조수, 보존처리된 과일 및 채소, 달걀, 유제품', 'GOODS'),
(30, '커피/차/빵/과자', '커피, 차, 코코아, 쌀, 파스타 및 국수, 빵, 페이스트리 및 과자', 'GOODS'),
(31, '농수산물/종자', '미가공 농업, 수산양식, 원예, 임업 생산물, 신선한 과실 및 채소', 'GOODS'),
(32, '음료/맥주', '맥주, 비알코올성 음료, 광천수 및 탄산수, 과실음료 및 주스', 'GOODS'),
(33, '주류', '알코올성 음료(맥주 제외), 음료제조용 알코올성 제제', 'GOODS'),
(34, '담배/흡연용품', '담배 및 대용담배, 권연 및 여송연, 전자담배 및 기화기, 흡연용구', 'GOODS'),

-- 서비스업 분류 (35-45류)
(35, '광고업/경영컨설팅업/도소매업', '광고, 사업관리, 사무관리, 도소매업, 온라인쇼핑몰업', 'SERVICES'),
(36, '보험/금융업', '보험업무, 금융업무, 화폐업무, 부동산업무', 'SERVICES'),
(37, '건설/수리업', '건축, 수리, 설치업무', 'SERVICES'),
(38, '통신업', '전기통신, 방송, 인터넷 서비스, 통신망 제공업', 'SERVICES'),
(39, '운송/여행업', '운송, 상품포장 및 보관, 여행주선', 'SERVICES'),
(40, '재료 가공/처리업', '재료처리, 가공업, 인쇄업, 폐기물처리업', 'SERVICES'),
(41, '교육/연예/스포츠업', '교육, 훈련, 오락, 스포츠 및 문화활동', 'SERVICES'),
(42, '과학/기술/디자인/연구개발업', '과학기술 서비스, 연구 및 설계, 컴퓨터 하드웨어 및 소프트웨어 설계 개발', 'SERVICES'),
(43, '숙박/음식점업', '음식점업, 숙박업, 임시숙박업', 'SERVICES'),
(44, '의료/미용/농업/원예업', '의료서비스, 수의과서비스, 위생 및 미용서비스, 농업 및 원예서비스', 'SERVICES'),
(45, '법률/보안/개인/사회 서비스업', '법률서비스, 보안서비스, 개인 및 사회서비스, 종교서비스', 'SERVICES');

-- ==========================================
-- 주요 유사군코드 서브 카테고리 삽입
-- ==========================================

-- ==========================================
-- 전체 1-45류 유사군코드 서브 카테고리 삽입 (각 카테고리당 최소 2개)
-- ==========================================

-- 1류: 화학제품
INSERT INTO sub_categories (code, name, description, main_category_id) VALUES
('G0101', '비료', '화학비료, 유기비료, 복합비료', 1),
('G0102', '화학제품', '공업용 화학품, 시약, 촉매', 1),

-- 2류: 페인트/니스
('G0201', '페인트', '건축용페인트, 자동차페인트, 방청페인트', 2),
('G0202', '염료/잉크', '직물염료, 인쇄잉크, 토너', 2),

-- 3류: 화장품/세제
('G1201', '화장품', '파운데이션, 립스틱, 아이섀도', 3),
('G1202', '세제', '세탁세제, 주방세제, 청소용세제', 3),

-- 4류: 연료/양초
('G0401', '연료', '가솔린, 경유, 등유', 4),
('G0402', '양초/왁스', '조명용양초, 장식양초, 밀랍', 4),

-- 5류: 약제/의료용품
('G0501', '의약품', '처방의약품, 일반의약품', 5),
('G0502', '의료용품', '의료용거즈, 반창고, 소독제', 5),

-- 6류: 금속제품
('G0601', '금속재료', '철강, 알루미늄, 구리', 6),
('G0602', '금속제품', '금속파이프, 철사, 못', 6),

-- 7류: 기계/공구
('G0701', '기계', '산업용기계, 제조장비', 7),
('G0702', '전동공구', '전기드릴, 전기톱, 연마기', 7),

-- 8류: 수공구
('G0801', '수공구', '망치, 드라이버, 스패너', 8),
('G0802', '칼류', '식칼, 가위, 면도기', 8),

-- 9류: 전자제품/소프트웨어
('G0901', '전자제품', '컴퓨터, 스마트폰, 태블릿', 9),
('G4201', '소프트웨어', '컴퓨터 프로그램, 애플리케이션', 9),

-- 10류: 의료기기
('G1001', '의료기기', '수술기구, 진단장비', 10),
('G1002', '의료용구', '의지, 의안, 의치', 10),

-- 11류: 조명/냉난방
('G1101', '조명기구', 'LED조명, 형광등, 백열등', 11),
('G1102', '냉난방기', '에어컨, 히터, 보일러', 11),

-- 12류: 운송기기
('G1201', '자동차', '승용차, 트럭, 버스', 12),
('G1202', '선박/항공기', '요트, 헬리콥터, 항공기', 12),

-- 13류: 화기/폭약
('G1301', '화기', '총기, 권총, 소총', 13),
('G1302', '폭약/폭죽', '화약, 폭죽, 불꽃놀이용품', 13),

-- 14류: 귀금속/액세서리
('G1401', '귀금속', '금, 은, 백금 제품', 14),
('G1402', '시계', '손목시계, 벽시계, 스톱워치', 14),

-- 15류: 악기
('G1501', '악기', '피아노, 기타, 바이올린', 15),
('G1502', '악기용품', '악보대, 튜너, 케이스', 15),

-- 16류: 종이/인쇄물
('G1601', '종이제품', '종이, 판지, 포장지', 16),
('G1602', '문방구', '펜, 연필, 지우개', 16),

-- 17류: 고무/플라스틱
('G1701', '고무제품', '고무호스, 고무패킹, 타이어', 17),
('G1702', '플라스틱', '플라스틱시트, 단열재', 17),

-- 18류: 가죽/가방
('G1801', '가죽제품', '가죽, 인조가죽, 모피', 18),
('G1802', '가방/지갑', '핸드백, 배낭, 지갑', 18),

-- 19류: 비금속 건축재료
('G1901', '건축재료', '콘크리트, 벽돌, 타일', 19),
('G1902', '비금속재료', '플라스틱파이프, 석재', 19),

-- 20류: 가구/목재
('G2001', '가구', '의자, 테이블, 침대', 20),
('G2002', '목재제품', '원목, 합판, 목재액자', 20),

-- 21류: 주방/생활용품
('G2101', '주방용구', '냄비, 프라이팬, 식기', 21),
('G2102', '청소용구', '걸레, 빗자루, 청소솔', 21),

-- 22류: 로프/섬유
('G2201', '로프/끈', '밧줄, 포장끈, 낚싯줄', 22),
('G2202', '섬유원료', '면화, 양모, 화학섬유', 22),

-- 23류: 실
('G2301', '방직용실', '면실, 견실, 모실', 23),
('G2302', '재봉용실', '재봉실, 자수실, 뜨개실', 23),

-- 24류: 직물/침구
('G2401', '직물', '면직물, 견직물, 모직물', 24),
('G2402', '침구류', '이불, 베개, 침대시트', 24),

-- 25류: 의류/신발/모자
('G4303', '의류', '셔츠, 바지, 드레스, 정장', 25),
('G4501', '신발류', '운동화, 구두, 부츠, 샌들', 25),
('G4502', '모자류', '야구모자, 비니, 햇, 헬멧', 25),

-- 26류: 액세서리/장식품
('G2601', '장식품', '단추, 지퍼, 레이스', 26),
('G2602', '머리장식', '헤어핀, 머리띠, 가발', 26),

-- 27류: 바닥재/벽지
('G2701', '바닥재', '카펫, 매트, 리놀륨', 27),
('G2702', '벽지/벽걸이', '벽지, 벽면장식재', 27),

-- 28류: 게임/완구/스포츠용품
('G2801', '완구/게임', '인형, 보드게임, 퍼즐', 28),
('G2802', '스포츠용품', '축구공, 테니스라켓, 골프채', 28),

-- 29류: 가공식품
('G2901', '육류/어류', '가공육, 통조림, 훈제식품', 29),
('G2902', '유제품', '우유, 치즈, 요구르트', 29),

-- 30류: 커피/차/빵/과자
('G0301', '빵/과자류', '빵, 케이크, 비스킷, 쿠키', 30),
('G0302', '면류', '라면, 국수, 파스타, 스파게티', 30),
('G0303', '시리얼류', '콘플레이크, 뮤즐리, 오트밀', 30),
('G0502', '커피/차류', '커피, 홍차, 녹차, 허브차', 30),

-- 31류: 농수산물/종자
('G3101', '농산물', '신선과일, 신선채소, 곡물', 31),
('G3102', '종자/묘목', '씨앗, 구근, 나무묘목', 31),

-- 32류: 음료/맥주
('G3201', '음료수', '탄산음료, 과일음료, 이온음료', 32),
('G3202', '맥주류', '맥주, 흑맥주, 무알코올 맥주', 32),

-- 33류: 주류
('G3301', '증류주', '소주, 위스키, 브랜디', 33),
('G3302', '발효주', '와인, 막걸리, 청주', 33),

-- 34류: 담배/흡연용품
('G3401', '담배', '궐련, 시가, 전자담배', 34),
('G3402', '흡연용구', '라이터, 재떨이, 파이프', 34),

-- 35류: 광고업/경영컨설팅업/도소매업 (서비스업)
('S120101', '광고업', '온라인광고, TV광고, 인쇄광고', 35),
('S120201', '도소매업', '온라인쇼핑몰, 백화점, 편의점', 35),

-- 36류: 보험/금융업 (서비스업)
('S120301', '보험업', '생명보험, 손해보험, 건강보험', 36),
('S120302', '금융업', '은행업, 투자업, 대출업', 36),

-- 37류: 건설/수리업 (서비스업)
('S120401', '건설업', '건축, 토목, 인테리어', 37),
('S120402', '수리업', '자동차수리, 가전수리, 시계수리', 37),

-- 38류: 통신업 (서비스업)
('S120501', '통신업', '이동통신, 인터넷, 케이블TV', 38),
('S120502', '방송업', 'TV방송, 라디오방송, 인터넷방송', 38),

-- 39류: 운송/여행업 (서비스업)
('S120601', '운송업', '택배, 물류, 대중교통', 39),
('S120602', '여행업', '여행사, 항공예약, 숙박예약', 39),

-- 40류: 재료 가공/처리업 (서비스업)
('S120701', '가공업', '금속가공, 플라스틱가공', 40),
('S120702', '인쇄업', '출판인쇄, 디지털인쇄, 복사업', 40),

-- 41류: 교육/연예/스포츠업 (서비스업)
('S120801', '교육업', '학원, 온라인교육, 직업훈련', 41),
('S120802', '오락업', '영화관, 놀이공원, 게임센터', 41),

-- 42류: 과학/기술/디자인/연구개발업 (서비스업)
('S120901', '연구개발업', '기술연구, 제품개발, R&D', 42),
('S120902', '디자인업', '제품디자인, 웹디자인, 그래픽디자인', 42),

-- 43류: 숙박/음식점업 (서비스업)
('S121001', '숙박업', '호텔, 모텔, 펜션', 43),
('S120602', '음식점업', '한식점, 중식점, 양식점, 카페', 43),

-- 44류: 의료/미용/농업/원예업 (서비스업)
('S121101', '의료업', '병원, 의원, 한의원', 44),
('S121102', '미용업', '미용실, 에스테틱, 네일아트', 44),

-- 45류: 법률/보안/개인/사회 서비스업 (서비스업)
('S121201', '법률업', '변호사, 변리사, 법무사', 45),
('S121202', '보안업', '경비업, 보안시스템, 탐정업', 45);

-- ==========================================
-- 상표 테스트 데이터
-- ==========================================
INSERT INTO trademarks (
    product_name, product_name_eng, application_number, application_date, 
    register_status, publication_number, publication_date, 
    registration_number, registration_date, created_by
) VALUES
('프레스카', 'FRESCA', '4019950043843', '1995-11-17', '등록', 
 '4019970001364', '1997-01-29', '4003600590000', '1997-04-17', 1),
 
('코카콜라', 'COCA COLA', '4019850012345', '1985-03-15', '등록',
 '4019850005678', '1985-06-01', '4001234567890', '1985-08-15', 1),
 
('삼성', 'SAMSUNG', '4019700001111', '1970-01-01', '등록',
 '4019700002222', '1970-03-01', '4000000111111', '1970-05-01', 1),
 
('네이버', 'NAVER', '4020000033333', '2000-12-01', '등록',
 '4020010044444', '2001-02-15', '4002000333333', '2001-04-01', 2),
 
('카카오톡', 'KAKAOTALK', '4020100055555', '2010-06-15', '등록',
 '4020100066666', '2010-08-30', '4003000555555', '2010-10-15', 2),

('애플', 'APPLE', '4019800077777', '1980-05-20', '등록',
 '4019810088888', '1981-01-10', '4001000777777', '1981-03-25', 1),

('아디다스', 'ADIDAS', '4019750099999', '1975-08-30', '등록',
 '4019760011111', '1976-02-15', '4000500999999', '1976-05-10', 2);

-- ==========================================
-- 상표-메인카테고리 연결 데이터 (중간테이블 활용)
-- ==========================================
INSERT INTO trademark_main_categories (trademark_id, main_category_id, priority_order, created_by) VALUES
-- 프레스카: 30류(주분류), 32류(부분류)
(1, 30, 1, 1), (1, 32, 2, 1),  
-- 코카콜라: 32류(주분류)
(2, 32, 1, 1),           
-- 삼성: 9류(주분류), 35류(부분류)
(3, 9, 1, 1), (3, 35, 2, 1),   
-- 네이버: 35류(주분류), 42류(부분류)
(4, 35, 1, 2), (4, 42, 2, 2),  
-- 카카오톡: 9류(주분류), 42류(부분류)
(5, 9, 1, 2), (5, 42, 2, 2),
-- 애플: 9류(주분류), 35류(부분류)
(6, 9, 1, 1), (6, 35, 2, 1),
-- 아디다스: 25류(주분류), 35류(부분류)
(7, 25, 1, 2), (7, 35, 2, 2);

-- ==========================================
-- 상표-서브카테고리 연결 데이터 (중간테이블 활용)
-- ==========================================
INSERT INTO trademark_sub_categories (trademark_id, sub_category_id, priority_order, created_by) VALUES
-- 프레스카: G0301(빵과자), G0303(시리얼), G0302(면류), G3201(음료수)
(1, (SELECT id FROM sub_categories WHERE code = 'G0301'), 1, 1),
(1, (SELECT id FROM sub_categories WHERE code = 'G0303'), 2, 1),
(1, (SELECT id FROM sub_categories WHERE code = 'G0302'), 3, 1),
(1, (SELECT id FROM sub_categories WHERE code = 'G3201'), 1, 1),

-- 코카콜라: G3201(음료수)
(2, (SELECT id FROM sub_categories WHERE code = 'G3201'), 1, 1),

-- 삼성: G0901(전자제품), S120101(광고업)
(3, (SELECT id FROM sub_categories WHERE code = 'G0901'), 1, 1),
(3, (SELECT id FROM sub_categories WHERE code = 'S120101'), 1, 1),

-- 네이버: S120101(광고업), S120901(연구개발업)
(4, (SELECT id FROM sub_categories WHERE code = 'S120101'), 1, 2),
(4, (SELECT id FROM sub_categories WHERE code = 'S120901'), 1, 2),

-- 카카오톡: G4201(소프트웨어), S120901(연구개발업)
(5, (SELECT id FROM sub_categories WHERE code = 'G4201'), 1, 2),
(5, (SELECT id FROM sub_categories WHERE code = 'S120901'), 1, 2),

-- 애플: G0901(전자제품), G4201(소프트웨어)
(6, (SELECT id FROM sub_categories WHERE code = 'G0901'), 1, 1),
(6, (SELECT id FROM sub_categories WHERE code = 'G4201'), 1, 1),

-- 아디다스: G4303(의류), G4501(신발류)
(7, (SELECT id FROM sub_categories WHERE code = 'G4303'), 1, 2),
(7, (SELECT id FROM sub_categories WHERE code = 'G4501'), 1, 2);

-- ==========================================
-- 성능 통계 업데이트
-- ==========================================
ANALYZE TABLE users, main_categories, sub_categories, trademarks, trademark_main_categories, trademark_sub_categories;

-- 초기화 완료 메시지
SELECT '상표등록 리서치 사이트 데이터베이스가 성공적으로 초기화되었습니다!' as message,
       '니스분류 1-45류 전체가 삽입되었습니다!' as categories_status,
       '다대다 관계는 중간테이블로 정규화되었습니다!' as relationship_status;