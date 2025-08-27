import re
import time
import random
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from fake_useragent import UserAgent
from api.driver_setup import start_xvfb, setup_driver


# xpath로 element 있는지 체크
def check_element(xP: str, driver) -> bool:
    try:
        return driver.find_element(By.XPATH, xP).is_enabled()
    except:
        return False

# css로 element 있는지 체크
def check_element_css(css: str, driver) -> bool:
    try:
        return driver.find_element(By.CSS_SELECTOR, css).is_enabled()
    except:
        return False

# 상품 코드 추출
def get_product_code(url: str) -> str:
    prod_code = url.split("products/")[-1].split("?")[0]
    return prod_code

# 별점 추출
def get_star_rating(element: str) -> float: 
    rating_percent = float(re.sub(r'[^0-9]', '', element))
    avg_rating = round((rating_percent / 20), 2) 
    return avg_rating

# 문자열에서 숫자 추출
def get_num_in_str(element: str) -> int:
    num = int(re.sub(r'[^0-9]', '', element))
    return num

def replace_thumbnail_size(url: str) -> str:
    
    return re.sub(r'/remote/[^/]+/image', '/remote/292x292ex/image', url)

# 리뷰 페이지 버튼 동작 컨트롤
def go_next_page(driver, page_num: int, review_id: str) -> bool:
    try:
        if review_id == "sdpReview":
            page_buttons = driver.find_element(By.XPATH, f'//*[@id="sdpReview"]/div/div[4]/div[2]/div/button[{page_num}]')
        else:
            page_buttons = driver.find_element(By.XPATH, f'//*[@id="btfTab"]/ul[2]/li[2]/div/div[6]/section[4]/div[3]/button[{page_num}]')
        
        # 처음 페이지 버튼을 누를 시 화면에 노출되야 클릭됨
        if page_num <= 3:
            driver.execute_script("arguments[0].scrollIntoView(true);", page_buttons)
            time.sleep(0.5)
            driver.execute_script("window.scrollBy(0, -150);")  # 살짝 위로 올려줌
            time.sleep(0.5)

        page_buttons.click()                               
        time.sleep(random.uniform(2,3))
        #print(f"[INFO] {product_code} 리뷰 {page_num-1} 페이지 이동")
        return True
    
    except:
        #print(f"[INFO] 리뷰 {page_num-1} 페이지 버튼 없음.")
        return False


# 상품 기본 정보 추출
def get_product_info(driver) -> dict:
    try:
        product_dict = dict()
        
        # 상품 판매 제목 추출
        title = driver.find_element(By.CSS_SELECTOR, 'h1.product-title').text
        product_dict['title'] = title

        # 상품 이미지 추출
        image_url = driver.find_element(By.CSS_SELECTOR, 'div.product-image img').get_attribute('src')
        product_dict['image_url'] = replace_thumbnail_size(image_url) # type: ignore


        # 카테고리 추출
        try:
            categorys = driver.find_elements(By.CSS_SELECTOR, 'ul.breadcrumb li')

            if not categorys:
                raise ValueError("카테고리 요소 없음")  # 강제로 예외 발생시켜 처리
            category_list = []
            
            for i in range(1, len(categorys)):
                category_list.append(categorys[i].text) 
                #product_dict[f'category{i}'] = categorys[i].text
                #print('category:',categorys[i].text)
            
            category_str = ','.join(category_list)
            product_dict['tag'] = category_str
        except Exception as e:
            print("[ERROR] 카테고리 추출 실패:",e)
        
        # 상품명 추출
        try:
            name = driver.find_element(By.CSS_SELECTOR, '#itemBrief > table > tbody > tr:nth-child(1) > td:nth-child(2)').text
            if "상품" == name[:2]:
                product_dict['name'] = title
            else:
                product_dict['name'] = name
        except NoSuchElementException as e:
            name = ''
            print("[ERROR] 상품명 추출 실패:",e)
        
        # 상품 코드 추출
        product_code = get_product_code(driver.current_url)
        product_dict['product_code'] = int(product_code)


        # 별점 추출
        try:
            el = driver.find_element(By.CSS_SELECTOR, 'span.rating-star-num').get_attribute("style")
            star_rating = get_star_rating(el)
            product_dict['star_rating'] = star_rating
            #print(star_rating)
        except NoSuchElementException as e:
            star_rating = 0.0
            print("[INFO] 별점 없음")

        # 리뷰 수 추출
        try:
            el = driver.find_element(By.CSS_SELECTOR, 'span.rating-count-txt').text
            review_count = get_num_in_str(el)
            product_dict['review_count'] = review_count
            #print('review_count:',review_count)
        except NoSuchElementException as e:
            review_count = ''
            print("[INFO] 리뷰 수 없음")

        # 할인 전 가격 추출
        try:
            sales_price = driver.find_element(By.CSS_SELECTOR, 'div.price-amount.sales-price-amount').text
            product_dict['sales_price'] = get_num_in_str(sales_price)
            #print('sales_price:',sales_price)
        except NoSuchElementException as e:
            product_dict['sales_price'] = 0
        except ValueError:
            product_dict['sales_price'] = 0
            print("[INFO] 할인 전 가격 없음")

        # 할인 후 가격 추출
        try:
            final_price = driver.find_element(By.CSS_SELECTOR, 'div.price-amount.final-price-amount').text
            product_dict['final_price'] = get_num_in_str(final_price)
            #print('final_price:',product_dict['final_price'])
        except NoSuchElementException as e:
            product_dict['final_price'] = 0
        except ValueError:
            product_dict['final_price'] = 0
            print("[INFO] 할인 후 가격 없음")

        return product_dict
    except Exception as e:
        print(f"[ERROR] 상품 기본 정보 추출 실패:",e)
        #driver.quit()
        return product_dict

# 상품 리뷰 추출
def get_product_review(driver, product_code):
    try:
        # 리뷰 최신순 정렬 (최신순 버튼 클릭)
        review_btn = driver.find_elements(By.CSS_SELECTOR, 'div.review-order-container button')
        review_btn[1].click()
        time.sleep(random.uniform(2,3))

        print(f"[INFO] {product_code} 리뷰 크롤링을 시작합니다.")

        # 리뷰 추출
        if check_element_css("#sdpReview article", driver):
            review_id = "sdpReview"
        else:
            review_id = "btfTab"

        product_list = []
        for p in range(2,12):
            try:
                articles = driver.find_elements(By.CSS_SELECTOR, f"#{review_id} article")

                for article in articles:
                    # 리뷰 별점 추출
                    review_rating = article.find_element(By.CSS_SELECTOR, '[data-rating]').get_attribute("data-rating")
                    
                    # 리뷰 날짜 추출
                    review_date = article.find_element(By.CSS_SELECTOR, 'div.sdp-review__article__list__info__product-info__reg-date').text
                    
                    # 리뷰 글 추출
                    content = ""
                    try:
                        review_contents = article.find_elements(By.CSS_SELECTOR, 'div.sdp-review__article__list__review__content')
                        for i, content_row in enumerate(review_contents):
                            if i == 0:
                                content += content_row.text
                            else:
                                content += ' ' + content_row.text
                    except NoSuchElementException:
                        print(f"[INFO] {product_code}리뷰가 없음:")
                    
                    # 사용자 조사(키워드) 추출
                    keywords = {} 
                    try:
                        survey_list = article.find_elements(By.CSS_SELECTOR, 'div.sdp-review__article__list__survey__row')
                        for survey_row in survey_list:
                            survey_span = survey_row.find_elements(By.CSS_SELECTOR,'span')
                            #print(survey_span[0].text, survey_span[1].text)
                            name = survey_span[0].text
                            tag = survey_span[1].text
                            keywords[name] = tag
                    except NoSuchElementException:
                        print('[INFO] Survey_list(keyword) 없음')

                    # 도움된 사람 수 추출
                    try:
                        review_help_cnt = article.find_element(By.CSS_SELECTOR, 'div.sdp-review__article__list__help').get_attribute("data-count")
                    except NoSuchElementException:
                        review_help_cnt = 0

                    product_list.append({
                        'product_code':product_code, 
                        'review_rating':review_rating, 
                        'review_date':review_date, 
                        'review_content':content,
                        'review_keywords':keywords,
                        'review_help_cnt': review_help_cnt
                        })
            except NoSuchElementException as e:
                print(f"[INFO] elements를 찾을 수 없음:", e)
                continue
            except Exception as e:
                print(f"[INFO] {product_code}리뷰 추출 실패:", e)
                continue
            
            next_page_success = go_next_page(driver, p+1, review_id)
            if not next_page_success:
                break
        return product_list
    except Exception as e:
        print(f"[ERROR] {product_code} 리뷰 추출 실패 :", e)
        return product_list

# 쿠팡 리뷰 크롤링 파이프라인 
def coupang_crawling(args) -> None:
    driver = None
    try:
        product_url, job_id = args
        driver = setup_driver()
        driver.get(product_url)
        product_code = get_product_code(driver.current_url)
        time.sleep(random.uniform(4, 5))

        # 상품 기본 정보 추출
        product_dict = get_product_info(driver)
        
        # 상품 리뷰 추출
        product_list = get_product_review(driver, product_code)
        
        # 상품 정보에 product_code 추가
        product_dict['product_code'] = product_code
        
        print("추출된 리뷰 개수:", len(product_list))
        
        # 리뷰 전송
        # kafka producer

        
        print(f'[INFO] {product_code} 리뷰 추출을 완료했습니다.')
    except Exception as e:
        print(f"[ERROR] {product_code} 에러 발생 :", e)
    finally:
        if driver:
            driver.quit()
        else:
            print("[INFO] driver is None")
        return



if __name__ == "__main__":
    #url = "https://www.coupang.com/vp/products/6224605496?itemId=12196225924&vendorItemId=85326747347&sourceType=srp_product_ads&clickEventId=4745aa00-8150-11f0-8196-f228a66d645a&korePlacement=15&koreSubPlacement=1&clickEventId=4745aa00-8150-11f0-8196-f228a66d645a&korePlacement=15&koreSubPlacement=1"
    url ="https://www.coupang.com/vp/products/4548468621?itemId=13569079594&vendorItemId=80822526378&pickType=COU_PICK&q=%EC%B2%AD%EC%86%8C%EA%B8%B0&searchId=d78155d52759146&sourceType=search&itemsCount=36&searchRank=6&rank=6"
    args = [url, 'a123']
    start_xvfb()
    coupang_crawling(args)


