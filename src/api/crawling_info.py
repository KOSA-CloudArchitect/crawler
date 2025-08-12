
# 상품 코드 추출
def get_product_code(url: str) -> str:
    prod_code = url.split("products/")[-1].split("?")[0]
    return prod_code

# 쿠팡 검색 후 상품 기본 정보 추출 
def get_product_links(keyword: str, max_links: int) -> list:

    driver = setup_driver()
    search_url = f"https://www.coupang.com/np/search?component=&q={keyword}"
    driver.get(search_url)
    time.sleep(random.uniform(3, 4))

    links = []
    duplicate_chk = set()
    try:
        items = driver.find_elements(By.CSS_SELECTOR, '#product-list li')
    except NoSuchElementException as e:
        print("[INFO] 검색된 상품이 없습니다.:", e)
        return []
    
    try:
        for item in items:
            
            # 링크 주소
            href = item.find_element(By.TAG_NAME, 'a').get_attribute('href')

            # 상품 코드 추출
            product_code = get_product_code(href)

            # 중복 확인
            if product_code in duplicate_chk:
                continue
            else:
                duplicate_chk.add(product_code)
            # # 이미지 주소
            # img = item.find_element(By.TAG_NAME, 'img').get_attribute('src')
            # # 상품 제목
            # title = item.find_elements(By.TAG_NAME, 'div')[2].text
            # # 최종 가격
            # price = item.find_element(By.TAG_NAME, 'strong').text
            # # 원래 가격
            # try:
            #     origin_price = item.find_element(By.TAG_NAME, 'del').text
            # except NoSuchElementException:
            #     origin_price = 0
            # 상품 별점, 리뷰 수
            try:
                product_info = item.find_elements(By.CSS_SELECTOR, '[data-sentry-component="ProductRating"] span')
            except NoSuchElementException:
                star_rating = 0
                review_count = 0
            # try:
            #     star_rating = product_info[0].find_element(By.CSS_SELECTOR, 'div').text
            # except NoSuchElementException:
            #     star_rating = 0
            try:
                review_count = get_num_in_str(product_info[1].text)
            except:
                review_count = 0
            
            # 특정 개수 이상의 리뷰가 있는 상품만 가져오기
            if review_count >= 200:
                links.append(href)
            
            if len(links) >= max_links:
                break
        print(f"[INFO] {len(links)}개 상품 url 추출 완료.")        
        #driver.quit()
        return links
    except Exception as e:
        print("[ERROR] 상품 url 추출 실패.:", e)
        return []
    finally:
        driver.quit()