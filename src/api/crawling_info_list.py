import re
import time
import random
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from api.driver_setup import start_xvfb, setup_driver

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
            
            # 링크 주소 추출 (다중 방법으로 시도)
            url = None
            try:
                url = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
            except NoSuchElementException:
                try:
                    url = item.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                except NoSuchElementException:
                    failed_count += 1
                    print("[INFO] 상품 url 추출 실패")
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
                title = item.find_elements(By.TAG_NAME, 'div')[2].text
            except (IndexError, NoSuchElementException):
                try:
                    title = item.find_element(By.CSS_SELECTOR, '.name').text
                except NoSuchElementException:
                    title = "제목 없음"
                    print("[INFO] 상품 제목 추출 실패")
                
            # 최종 가격
            try:
                final_price = item.find_element(By.TAG_NAME, 'strong').text
            except NoSuchElementException:
                final_price = 0
                print("[INFO] 최종 가격 없음")

            # 원래 가격
            try:
                origin_price = item.find_element(By.TAG_NAME, 'del').text
            except NoSuchElementException:
                #print("[INFO] 원래 가격 없음")
                origin_price = 0
                    
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
                print(f"[INFO] {i}번째 상품 처리 성공 (리뷰 {review_count}개)")
            else:
                failed_count += 1
                print(f"[INFO] {i}번째 상품 제외 (리뷰 {review_count}개, 200개 미만)")
            
            if len(result_list) >= max_links:
                break
    
        print(f"[INFO] 상품 처리 완료 - 총 {total_items}개, 성공 {success_count}개, 실패 {failed_count}개")
        print(f"[INFO] {len(result_list)}개 상품 추출 완료.")        
        return result_list
    except Exception as e:
        print("[ERROR] 상품 url 추출 실패.:", e)
        return []
    finally:
        driver.quit()



if __name__ == "__main__":
    keyword = "선풍기"
    max_links = 20
    result = get_info_list(keyword,max_links)
    print(result)


