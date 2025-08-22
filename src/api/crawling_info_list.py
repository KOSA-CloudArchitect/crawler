import re
import time
import random
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from chromedriver import is_xvfb_running, start_xvfb, setup_driver

# 상품 코드 추출
def get_product_code(url: str) -> str:
    prod_code = url.split("products/")[-1].split("?")[0]
    return prod_code

# 이미지 사이즈 변경
def replace_thumbnail_size(url: str) -> str:
    return re.sub(r'/remote/[^/]+/image', '/remote/292x292ex/image', url)

# 문자열에서 숫자 추출
def get_num_in_str(element: str) -> int:
    num = int(re.sub(r'[^0-9]', '', element))
    return num

# 쿠팡 검색 후 상품 기본 정보 추출 
def get_product_links(keyword: str, max_links: int) -> list:

    start_xvfb()
    driver = setup_driver()
    search_url = f"https://www.coupang.com/np/search?component=&q={keyword}"
    driver.get(search_url)
    time.sleep(random.uniform(3, 4))
    driver.save_screenshot("screenshot.png")

    result_list = []
    duplicate_chk = set()
    result_dict = {}
    try:
        items = driver.find_elements(By.CSS_SELECTOR, '#product-list li')
    except NoSuchElementException as e:
        print("[INFO] 검색된 상품이 없습니다.:", e)
        return []
    
    try:
        for item in items:
            result_dict = {}
            
            # 링크 주소
            try:
                url = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
            except NoSuchElementException:
                print("[INFO] 상품 url 추출 실패")
                break

            # 상품 코드 추출
            product_code = get_product_code(url)

            # 중복 확인
            if product_code in duplicate_chk:
                continue
            else:
                duplicate_chk.add(product_code)
            # 이미지 주소
            img = item.find_element(By.TAG_NAME, 'img').get_attribute('src')
            img = replace_thumbnail_size(img)
            # 상품 제목
            title = item.find_elements(By.TAG_NAME, 'div')[2].text
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
                print("[INFO] 원래 가격 없음")
                origin_price = 0
            # 리뷰 수 추출
            try:
                # class 속성에 특정 문자열 포함 조건
                review_count = driver.find_element(By.XPATH, '//span[contains(@class, "ProductRating_ratingCount")]')
                review_count = get_num_in_str(review_count.text)
            except NoSuchElementException:
                print("[INFO] 리뷰 수 데이터를 찾지 못했습니다.")
                review_count = 0
            
            # 별점 추출
            try:
                # class 속성에 특정 문자열 포함 조건
                review_rating = driver.find_element(By.XPATH, '//span[contains(@class, "ProductRating_rating")]')
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
            
            if len(result_list) >= max_links:
                break
    
        print(f"[INFO] {len(result_list)}개 상품 추출 완료.")        
        #driver.quit()
        return result_list
    except Exception as e:
        print("[ERROR] 상품 url 추출 실패.:", e)
        return []
    finally:
        driver.quit()



if __name__ == "__main__":

    keyword = "휴지"
    max_links = 10
    result = get_product_links(keyword,max_links)

    print(result)


