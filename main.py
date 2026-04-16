import json
import time

EPSILON = 1e-9

perf_stats = {}  # size: [time, time, ...]
generated_cross = None
generated_x = None
generated_n = None


# -------------------------------
# 입력 처리
# -------------------------------
def input_matrix(n):
    matrix = []

    row_idx = 0
    while row_idx < n:
        user_input = input().strip()

        # 1. 빈 입력 체크
        if not user_input:
            print(f"입력 형식 오류: 각 줄에 {n}개의 숫자를 공백으로 입력하세요.")
            continue

        parts = user_input.split()

        # 2. 개수 체크
        if len(parts) != n:
            print(f"입력 형식 오류: 각 줄에 {n}개의 숫자를 공백으로 입력하세요.")
            continue

        # 3. 숫자 파싱 체크
        try:
            row = [float(x) for x in parts]
        except ValueError:
            print(f"입력 형식 오류: 숫자만 입력하세요.")
            continue

        matrix.append(row)
        row_idx += 1

    return matrix


# -------------------------------
# 유효성 검사
# -------------------------------
def validate_matrix(mat, n):
    if len(mat) != n:
        return False
    for row in mat:
        if len(row) != n:
            return False
    return True


# -------------------------------
# MAC 연산
# -------------------------------
def mac_operation(pattern, flt):
    total = 0.0
    for i in range(len(pattern)):
        for j in range(len(pattern)):
            total += pattern[i][j] * flt[i][j]
    return total


# -------------------------------
# 점수 비교
# -------------------------------
def decide(score_cross, score_x):
    if abs(score_cross - score_x) < EPSILON:
        return "UNDECIDED"
    return "Cross" if score_cross > score_x else "X"


# -------------------------------
# 라벨 정규화
# -------------------------------
def normalize_label(label):
    label = str(label).lower()
    if label in ['+', 'cross']:
        return "Cross"
    elif label in ['x']:
        return "X"
    return None


# -------------------------------
# 시간 측정
# -------------------------------
def measure_time(pattern, flt, repeat=10):
    start = time.perf_counter()
    for _ in range(repeat):
        mac_operation(pattern, flt)
    end = time.perf_counter()
    return (end - start) / repeat * 1000


# -------------------------------
# 성능 출력
# -------------------------------
def print_performance():
    print("\n#---------------------------------------")
    print("# [성능 분석 (평균/10회)]")
    print("#---------------------------------------")
    print("크기\t평균 시간(ms)\t연산 횟수")
    print("-------------------------------------")

    for n in [3, 5, 13, 25]:
        pattern = [[1.0]*n for _ in range(n)]
        flt = [[1.0]*n for _ in range(n)]
        t = measure_time(pattern, flt)
        print(f"{n}x{n}\t{t:.3f}\t\t{n*n}")

def run_manual_mode():
    global generated_cross, generated_x, generated_n

    print("\n[패턴 입력 방식]")
    print("1. 직접 입력")
    print("2. 생성된 패턴 사용")

    while True:
        choice = input("선택: ")

        # ✅ 생성된 패턴 사용
        if choice == "2":
            if generated_cross is None:
                print("❗ 생성된 패턴이 없습니다. 먼저 패턴 생성기를 실행하세요.")
                continue  # 다시 선택하게
            else:
                print("\n✔ 생성된 패턴 사용")

                filter_a = generated_cross
                filter_b = generated_x
                n = generated_n
                print(f"패턴 입력({n})")
                pattern = input_matrix(n)
                break

        # ✅ 직접 입력
        elif choice == "1":
            print("\n필터 Cross (3줄 입력)")
            filter_a = input_matrix(3)

            print("필터 X (3줄 입력)")
            filter_b = input_matrix(3)

            print("패턴 입력")
            pattern = input_matrix(3)

            n = 3
            break

        else:
            print("잘못된 입력입니다. 다시 선택하세요.")

    # MAC 수행
    score_a = mac_operation(pattern, filter_a)
    score_b = mac_operation(pattern, filter_b)

    result = decide(score_a, score_b)

    print(f"Cross 점수: {score_a}")
    print(f"X 점수: {score_b}")
    print(f"판정: {result}")

    print_single_performance(n, pattern, filter_a)



# -------------------------------
# JSON 로드
# -------------------------------
def load_json():
    with open("data.json", "r") as f:
        return json.load(f)


# -------------------------------
# JSON 모드
# -------------------------------
def run_json_mode():
    data = load_json()

    print("\n# [1] 필터 로드")
    filters = data.get("filters", {})
    filter_map = {}

    for key, val in filters.items():
        try:
            #size = int(key.split("_")[1])
            if not key.startswith("size_"):
                raise Exception("잘못된 키 형식")
            
            parts = key.split("_")
            if len(parts) < 2 or not parts[1].isdigit():
                raise Exception("잘못된 키 형식")
            size = int(parts[1])  # size_3_float_1 → 3
            cross = val.get("cross")
            x = val.get("x")

            if not cross or not x:
                raise Exception("필터 누락")

            filter_map[size] = {"Cross": cross, "X": x}
            print(f"✓ size_{size} 필터 로드 완료")
        except:
            print(f"✗ {key} 로드 실패")

    print("\n# [2] 패턴 분석")

    patterns = data.get("patterns", {})
    total = passed = failed = 0
    fail_cases = []

    for key, val in patterns.items():
        total += 1
        print(f"\n--- {key} ---")

        try:
            

            size = int(key.split("_")[1])
            pattern = val["input"]
            expected = normalize_label(val["expected"])

            if len(pattern) != size:
                
                raise Exception("크기 불일치 오류")

            if expected is None:
                raise Exception("라벨 오류")

            if size not in filter_map:
                raise Exception("필터 없음")

            flt_cross = filter_map[size]["Cross"]
            flt_x = filter_map[size]["X"]

            if not (validate_matrix(pattern, size) and
                    validate_matrix(flt_cross, size) and
                    validate_matrix(flt_x, size)):
                raise Exception("크기 불일치")
            
            t = measure_time(pattern, flt_cross)

            # 누적
            if size not in perf_stats:
                perf_stats[size] = []

            perf_stats[size].append(t)

            sc = mac_operation(pattern, flt_cross)
            sx = mac_operation(pattern, flt_x)

            result = decide(sc, sx)

            print(f"Cross 점수: {sc}")
            print(f"X 점수: {sx}")

            if result == expected:
                print(f"판정: {result} | expected: {expected} | PASS")
                passed += 1
            else:
                print(f"판정: {result} | expected: {expected} | FAIL")
                failed += 1
                fail_cases.append((key, "판정 불일치"))

        except Exception as e:
            print(f"FAIL ({e})")
            failed += 1
            fail_cases.append((key, str(e)))

    print("\n#---------------------------------------")
    print("# [성능 분석 (크기별 평균)]")
    print("#---------------------------------------")

    print("크기\t평균 시간(ms)\t연산 횟수")
    print("-------------------------------------")

    for n in sorted(perf_stats.keys()):
        times = perf_stats[n]
        avg = sum(times) / len(times)
        print(f"{n}x{n}\t{avg:.3f}\t\t{n*n}")

    #print_performance()

    print("\n# [결과 요약]")
    print(f"총 테스트: {total}")
    print(f"통과: {passed}")
    print(f"실패: {failed}")

    if fail_cases:
        print("\n실패 케이스:")
        for c, r in fail_cases:
            print(f"- {c}: {r}")

def print_single_performance(n, pattern, flt):
    print("\n#---------------------------------------")
    print("# [성능 분석 - 현재 연산 기준]")
    print("#---------------------------------------")

    t = measure_time(pattern, flt)

    print("크기\t평균 시간(ms)\t연산 횟수")
    print("-------------------------------------")
    print(f"{n}x{n}\t{t:.3f}\t\t{n*n}")

def flatten(matrix):
    return [elem for row in matrix for elem in row]


def mac_operation_1d(pattern_1d, filter_1d):
    total = 0.0
    for i in range(len(pattern_1d)):
        total += pattern_1d[i] * filter_1d[i]
    return total


def run_optimization_mode():
    print("\n# [최적화 성능 비교]")

    n = int(input("크기 N 입력: "))

    pattern = generate_cross(n)
    flt = generate_cross(n)

    repeat = 10

    # 2D
    start = time.perf_counter()
    for _ in range(repeat):
        mac_operation(pattern, flt)
    end = time.perf_counter()
    t2d = (end - start) / repeat * 1000

    # 1D
    p1d = flatten(pattern)
    f1d = flatten(flt)

    start = time.perf_counter()
    for _ in range(repeat):
        mac_operation_1d(p1d, f1d)
    end = time.perf_counter()
    t1d = (end - start) / repeat * 1000

    print("\n구분\t평균 시간(ms)")
    print("----------------------")
    print(f"2D\t{t2d:.3f}")
    print(f"1D\t{t1d:.3f}")

def generate_cross(n):
    mat = [[0]*n for _ in range(n)]
    mid = n // 2
    for i in range(n):
        mat[mid][i] = 1
        mat[i][mid] = 1
    return mat


def generate_x(n):
    mat = [[0]*n for _ in range(n)]
    for i in range(n):
        mat[i][i] = 1
        mat[i][n-i-1] = 1
    return mat


def run_generator_mode():
    global generated_cross, generated_x, generated_n

    print("\n# [패턴 생성기]")

    n = int(input("크기 N 입력: "))

    generated_cross = generate_cross(n)
    generated_x = generate_x(n)
    generated_n = n

    print("\nCross 패턴:")
    for row in generated_cross:
        print(row)

    print("\nX 패턴:")
    for row in generated_x:
        print(row)

    print("\n✔ 생성된 패턴이 저장되었습니다 (모드1/최적화에서 사용 가능)")



# -------------------------------
# 메인
# -------------------------------
def main():
    while True:

        print("=== Mini NPU Simulator ===")
        print("1. 사용자 입력 (base 3x3)")
        print("2. data.json 분석")
        print("3. 최적화 성능 비교")
        print("4. 패턴 생성기")
        print("5. 종료")

        choice = input("선택: ")

        if choice == "1":
            run_manual_mode()
        elif choice == "2":
            run_json_mode()
        elif choice == "3":
            run_optimization_mode()
        elif choice == "4":
            run_generator_mode()
        elif choice == "5":
            quit()
        else:
            print("잘못된 입력입니다.")


if __name__ == "__main__":
    main()