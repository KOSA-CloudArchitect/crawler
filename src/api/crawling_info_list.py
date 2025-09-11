import re
import time
import random
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from api.driver_setup import start_xvfb, setup_driver
import traceback

# 아이템 블록에서 가능한 URL을 모두 수집하고 제품 URL을 우선 선택
def extract_item_url(item):
    try:
        anchors = item.find_elements(By.XPATH, './/a[@href]')
    except Exception as e:
        # print(f"[DEBUG] anchors 조회 실패: {e}")
        return None

    candidates = []
    for a in anchors:
        try:
            href = a.get_attribute('href') or ''
            if href:
                candidates.append(href.strip())
        except Exception:
            continue

    # print(f"[DEBUG] url candidates count: {len(candidates)}")
    if not candidates:
        return None

    product_candidates = [u for u in candidates if '/vp/products/' in u]
    chosen = product_candidates[0] if product_candidates else candidates[0]

    if chosen.startswith('/'):
        chosen = 'https://www.coupang.com' + chosen

    if not chosen.startswith('http'):
        # print(f"[DEBUG] 비정상 href 필터: {chosen}")
        return None

    # print(f"[DEBUG] 선택된 URL: {chosen}")
    return chosen

# 라인 단위로 "숫자로 시작하고 '원'으로 끝나는" 가격만 추출
def extract_prices_kr(text: str) -> list:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    pattern = re.compile(r'^(?=\d)[\d,]+원$')
    results = []
    for line in lines:
        if pattern.match(line):
            try:
                results.append(int(line[:-1].replace(',', '')))
            except ValueError:
                continue
    return results

# 상품 코드 추출
def get_product_code(url: str) -> str:
    prod_code = url.split("products/")[-1].split("?")[0]
    return prod_code

# 이미지 사이즈 변경
def replace_thumbnail_size(url: str) -> str:
    return re.sub(r'/remote/[^/]+/image', '/remote/292x292ex/image', url)

# 문자열에서 숫자 추출
def get_num_in_str(element: str) -> int:
    # 빈 문자열이나 None 체크
    if not element or element.strip() == '':
        return 0
    
    # 숫자만 추출
    numbers = re.sub(r'[^0-9]', '', element)
    
    # 숫자가 없으면 0 반환
    if not numbers:
        return 0
    
    try:
        return int(numbers)
    except ValueError:
        return 0

# 쿠팡 검색 후 상품 기본 정보 추출 
def get_info_list(keyword: str, max_links: int) -> list:
    start_xvfb()
    print(keyword,max_links)
    driver = setup_driver()
    search_url = f"https://www.coupang.com/np/search?component=&q={keyword}"
    driver.get(search_url)
    time.sleep(random.uniform(5, 6))
    #driver.save_screenshot("screenshot.png")

    result_list = []
    duplicate_chk = set()
    try:
        items = driver.find_elements(By.CSS_SELECTOR, '#product-list li')
    except NoSuchElementException as e:
        print("[INFO] 검색된 상품이 없습니다.:", e)

    # 상품이 없으면 재시도 로직
    if len(items) == 0:
        max_retries = 3
        retry_count = 0

        while len(items) == 0 and retry_count < max_retries:
            retry_count += 1
            print(f"[INFO] 상품이 없습니다. {retry_count}번째 재시도 중... (최대 {max_retries}회)")
            
            # 페이지 새로고침
            driver.refresh()
            time.sleep(random.uniform(3, 4))
            
            # 기존 CSS 선택자로 상품 찾기
            try:
                items = driver.find_elements(By.CSS_SELECTOR, '#product-list li')
                print(f"[INFO] 재시도 후 상품 개수: {len(items)}")
            except NoSuchElementException as e:
                print(f"[INFO] {retry_count}번째 재시도 실패:", e)
                items = []
            
            # 여전히 상품이 없으면 잠시 대기 후 재시도
            if len(items) == 0:
                print(f"[INFO] {retry_count}번째 재시도 실패, 잠시 대기 후 재시도...")
                time.sleep(random.uniform(2, 3))
        
        # 모든 재시도 후에도 상품이 없으면 빈 리스트 반환
        if len(items) == 0:
            print(f"[ERROR] {max_retries}회 재시도 후에도 상품을 찾을 수 없습니다.")
            return []
        
        print(f"[INFO] 최종 상품 개수: {len(items)}")


    try:
        success_count = 0
        failed_count = 0
        total_items = len(items)

        for i, item in enumerate(items):
            result_dict = {}
            
            # 링크 주소 추출 (모든 a[href] 후보에서 선택)
            url = extract_item_url(item)
            if not url:
                failed_count += 1
                try:
                    snippet = item.get_attribute("innerHTML")[:400]
                    #print(f"[DEBUG] item innerHTML snippet: {snippet}")
                except Exception:
                    pass
                print("[INFO] 상품 url 추출 실패해 다음 상품으로 넘어갑니다.")
                continue

            # 상품 코드 추출
            product_code = get_product_code(url)

            # 중복 확인
            if product_code in duplicate_chk:
                continue
            else:
                duplicate_chk.add(product_code)
                    
            # 이미지 주소
            try:
                img = item.find_element(By.TAG_NAME, 'img').get_attribute('src')
                img = replace_thumbnail_size(img)
            except NoSuchElementException:
                img = ""
                print("[INFO] 이미지 주소 추출 실패")
                
            # 상품 제목
            try:
                title = item.find_element(By.XPATH, './/div[contains(@class, "ProductUnit_productName")]').text
            except (NoSuchElementException):
                try:
                    title = item.find_element(By.CSS_SELECTOR, '.name').text
                except NoSuchElementException:
                    title = "제목 없음"
                    print("[INFO] 상품 제목 추출 실패")
                
            # 가격 추출
            final_price = 0
            origin_price = 0

            price_element = item.find_element(By.XPATH, './/div[contains(@class, "PriceArea_priceArea")]')
            # 최종 가격
            try:
                final_price = get_num_in_str(price_element.find_element(By.XPATH, ".//div[contains(text(),'원')]").text)
 
            except NoSuchElementException as e:
                final_price = 0

            # 원래 가격 (취소선 del)
            try:
                origin_price = get_num_in_str(price_element.find_element(By.XPATH, ".//del[contains(text(),'원')]").text)
            except NoSuchElementException:
                origin_price = 0  # 원가 없을 수 있음(세일가만 노출)
            
            # 가격 정보를 못찾을 경우: price_element.text에서 폴백 파싱 (라인 기반)
            if final_price == 0:
                print("[INFO] 가격 정보를 못찾아 폴백 파싱 중...")
                raw_price_text = price_element.text
                # print(f"[DEBUG] 폴백 후보(raw_price_text): {raw_price_text}")
                extracted = extract_prices_kr(raw_price_text)
                # print(f"[DEBUG] 라인기반 추출 결과: {extracted}")

                if len(extracted) >= 2:
                    origin_price = extracted[0]
                    final_price = extracted[-1]
                    print(f"[INFO] 폴백 파싱 성공: origin_price={origin_price}, final_price={final_price}")
                elif len(extracted) == 1:
                    final_price = extracted[0]
                    origin_price = 0
                    print(f"[INFO] 폴백 파싱 성공: final_price={final_price}")
                else:
                    # 최후의 보루: 임의 숫자 토큰에서 마지막 값을 최종가로 시도
                    any_numbers = re.findall(r'\d+', raw_price_text)
                    if any_numbers:
                        try:
                            final_price = int(any_numbers[-1])
                            print(f"[INFO] 폴백 파싱 성공: final_price={final_price} (숫자 토큰)")
                        except ValueError:
                            final_price = 0
                            origin_price = 0
                if final_price == 0:
                    print(f"[WARN] 폴백 파싱 실패: raw='{raw_price_text}'")

            # 폴백 후에도 가격이 모두 없으면 스킵
            if final_price == 0:
                print("[INFO] 가격 정보를 못찾아 다음 상품으로 넘어갑니다.")
                continue
            #print(f"[INFO] 가격 정보 추출 완료: origin_price={origin_price}, final_price={final_price}")
                              
            # 리뷰 수 추출
            try:
                # 상대 경로로 변경하여 각 상품 내에서만 검색
                review_count = item.find_element(By.XPATH, './/span[contains(@class, "ProductRating_ratingCount")]')
                review_count = get_num_in_str(review_count.text)
            except NoSuchElementException:
                print("[INFO] 리뷰 수 데이터를 찾지 못했습니다.")
                review_count = 0
                
            # 별점 추출
            try:
                # 상대 경로로 변경하여 각 상품 내에서만 검색
                review_rating = item.find_element(By.XPATH, './/span[contains(@class, "ProductRating_rating")]')
                review_rating = review_rating.text
            except NoSuchElementException:
                review_rating = 0
                print("[INFO] 별점 데이터를 찾지 못했습니다.")

                
            result_dict['url'] = url
            result_dict['product_code'] = product_code
            result_dict['img'] = img
            result_dict['title'] = title
            result_dict['final_price'] = final_price
            result_dict['origin_price'] = origin_price
            result_dict['review_count'] = review_count
            result_dict['review_rating'] = review_rating
            
            # 특정 개수 이상의 리뷰가 있는 상품만 가져오기
            if review_count >= 200:
                result_list.append(result_dict)
                success_count += 1
                print(f"[INFO] {i+1}번째 상품 처리 성공 (리뷰 {review_count}개)")
            else:
                failed_count += 1
                print(f"[INFO] {i+1}번째 상품 제외 (리뷰 {review_count}개, 200개 미만)")
            
            if len(result_list) >= max_links:
                break
    
        print(f"[INFO] 상품 처리 완료 - 총 {total_items}개, 성공 {success_count}개, 실패 {failed_count}개")
        print(f"[INFO] {len(result_list)}개 상품 추출 완료.")        
        return result_list
    except Exception as e:
        print("[ERROR] 상품 url 추출 실패.:", e)
        traceback.print_exc()
        return []
    finally:
        driver.quit()



if __name__ == "__main__":
    keyword = "선풍기"
    max_links = 5
    result = get_info_list(keyword,max_links)
    print(result)


