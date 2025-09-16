import re
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
#from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, StaleElementReferenceException,
    ElementClickInterceptedException, NoSuchElementException
)
from fake_useragent import UserAgent
from api.driver_setup import start_xvfb, setup_driver
from api.kafka_producer import send_to_kafka_bridge
from api.multi_xvfb import xvfb_display
import traceback
from datetime import datetime, timezone, timedelta
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    ZoneInfo = None  # tzdata 미설치 시 폴백 사용

# KST(Asia/Seoul) 현재 시각 ISO 문자열 생성
def _now_kst_iso() -> str:
    try:
        if ZoneInfo is not None:
            return datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
    except Exception:
        pass
    # 폴백: 고정 오프셋 +09:00
    return datetime.now(timezone(timedelta(hours=9))).isoformat()

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

# 사람같은 미세 지연
def _human_pause(min_s: float = 0.15, max_s: float = 0.35) -> None:
    time.sleep(random.uniform(min_s, max_s))

# 요소를 화면 중앙 부근으로 부드럽게 노출
def _gently_scroll_into_view(driver, element) -> None:
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        _human_pause(0.2, 0.4)
        # 미세 스크롤 보정
        jitter = random.randint(-80, -40)
        driver.execute_script("window.scrollBy(0, arguments[0]);", jitter)
        _human_pause(0.1, 0.25)
    except Exception:
        pass

# 요소 위로 살짝 마우스 이동(호버)
def _hover_element(driver, element) -> None:
    try:
        actions = ActionChains(driver)
        actions.move_to_element(element).perform()
        _human_pause(0.1, 0.3)
        try:
            # 아주 작은 오프셋으로 자연스러운 움직임
            offset_x = random.randint(-3, 3)
            offset_y = random.randint(-2, 2)
            actions.move_by_offset(offset_x, offset_y).perform()
            _human_pause(0.05, 0.15)
            actions.move_by_offset(-offset_x, -offset_y).perform()
        except Exception:
            pass
    except Exception:
        pass

# 클릭 시도 안정화
def _safe_click(element, driver, retries: int = 2) -> bool:
    for _ in range(retries + 1):
        try:
            element.click()
            return True
        except (ElementClickInterceptedException, StaleElementReferenceException):
            _human_pause(0.2, 0.5)
            try:
                driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                _human_pause(0.2, 0.4)
        except Exception:
            _human_pause(0.2, 0.4)
    return False

# 리뷰 10 페이지 넘기는 버튼 동작 컨트롤
def new_go_next_10_page(driver, page_num: int):
    try:
        for _ in range(page_num):

            next_btn = driver.find_element(By.CSS_SELECTOR, "button.js_reviewArticlePageNextBtn")
            if not next_btn.get_attribute("disabled"):
                next_btn.click()
                time.sleep(random.uniform(2,3))
            else:
                print("버튼이 비활성화(Disabled) 상태입니다.")
                return False
        if page_num > 1:
            print(f"[INFO] 10페이지 {page_num}번 넘기기 버튼 클릭 성공")
        elif page_num == 1:
            print(f"[INFO] 10페이지 넘기기 버튼 클릭 성공")
        return True

    except NoSuchElementException:
        print("[INFO] 마지막 페이지 - 더 이상 10페이지 넘기기 버튼이 없습니다")
        return False

# 리뷰 10 페이지 넘기는 버튼 동작 컨트롤
def go_next_10_page(driver, page_num, container_id):
    
    try:
        for _ in range(page_num):
            if container_id == "sdpReview":
                next_button = driver.find_element(By.XPATH, '//*[@id="sdpReview"]/div/div[4]/div[2]/div/button[12]')
            else:
                next_button = driver.find_element(By.XPATH, f'//*[@id="btfTab"]/ul[2]/li[2]/div/div[6]/section[4]/div[3]/button[12]')
  
            if next_button.is_enabled():
                _gently_scroll_into_view(driver, next_button)
                _hover_element(driver, next_button)
                try:
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(next_button))
                except Exception:
                    pass

                if not _safe_click(next_button, driver):
                    return False

                time.sleep(random.uniform(2,3))
                _human_pause(0.15, 0.3)
                
            else:
                print("버튼이 비활성화(Disabled) 상태입니다.")
                return False
        if page_num >= 1:
            print(f"[INFO] 10페이지 {page_num}번 넘기기 버튼 클릭 성공")
        return True
    except NoSuchElementException:
        print("[INFO] 마지막 페이지 - 더 이상 10페이지 넘기기 버튼이 없습니다")
        return False

# 리뷰 페이지 버튼 동작 컨트롤
def go_next_page(driver, page_num: int, review_id: str) -> bool:
    try:
        if review_id == "sdpReview":
            page_buttons = driver.find_element(By.XPATH, f'//*[@id="sdpReview"]/div/div[4]/div[2]/div/button[{page_num}]')
        else:
            page_buttons = driver.find_element(By.XPATH, f'//*[@id="btfTab"]/ul[2]/li[2]/div/div[6]/section[4]/div[3]/button[{page_num}]')
        
        # 처음 몇 페이지는 버튼이 화면 하단에 걸려 클릭 실패 가능성 -> 사람처럼 정렬 및 호버
        if page_num <= 3:
            _gently_scroll_into_view(driver, page_buttons)
            _hover_element(driver, page_buttons)
        else:
            # 그 외 페이지도 너무 부자연스럽지 않게 가볍게 호버만
            _hover_element(driver, page_buttons)

        time.sleep(random.uniform(2,3))

        if not _safe_click(page_buttons, driver):
            return False

        time.sleep(random.uniform(2,3))
        #print(f"[INFO] {product_code} 리뷰 {page_num-1} 페이지 이동")
        return True
    
    except NoSuchElementException:
        #print(f"[INFO] 리뷰 {page_num-1} 페이지 버튼 없음.")
        return False
def find_review_page_button(driver, page_num: int):
    page_str = str(page_num)
    try:
        # 가장 안정적인: data-page 속성
        return driver.find_element(By.CSS_SELECTOR, f"button.js_reviewArticlePageBtn[data-page='{page_str}']")
    except NoSuchElementException:
        pass

    # Fallback: 텍스트 매칭
    try:
        return driver.find_element(By.XPATH, f"//button[contains(@class,'js_reviewArticlePageBtn')][normalize-space(text())='{page_str}']")
    except NoSuchElementException:
        pass

    # 최후: JS로 전수조사
    el = driver.execute_script("""
        const p = arguments[0];
        return [...document.querySelectorAll('button')].find(b => 
            (b.dataset.page || '').trim() === p || 
            (b.textContent || '').trim() === p
        ) || null;
    """, page_str)
    if el:
        return el

    raise NoSuchElementException(f"리뷰 페이지 버튼 {page_num} 없음")


def click_next_review_page(driver, page_num: int):
    try:
        btn = find_review_page_button(driver, page_num)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        time.sleep(random.uniform(1,2))
        btn.click()
        time.sleep(random.uniform(2,3))  # 로딩 대기
        print(f"[INFO] {page_num} 페이지 버튼 클릭 성공")
        return True
    except Exception as e:
        print(f"[WARN] 최신 방법으로 {page_num} 페이지 버튼 클릭 실패: {e}")

        return False
        
# 상품 기본 정보 추출
def get_product_info(driver) -> dict:
    try:
        product_dict = dict()
        
        #상품 판매 제목 추출

        try:
            title = driver.find_element(By.CSS_SELECTOR, 'h1.product-title').text
            product_dict['title'] = title
        except NoSuchElementException as e:
            product_dict['title'] = ''
            print("[INFO] 상품 판매 제목 추출 실패:",e)

        # # 상품 이미지 추출
        # image_url = driver.find_element(By.CSS_SELECTOR, 'div.product-image img').get_attribute('src')
        # product_dict['image_url'] = replace_thumbnail_size(image_url) # type: ignore


        # 카테고리 추출
        try:
            WAIT = WebDriverWait(driver, 15)
            WAIT.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'ul.breadcrumb li')
            ))
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
        # try:
        #     name = driver.find_element(By.CSS_SELECTOR, '#itemBrief > table > tbody > tr:nth-child(1) > td:nth-child(2)').text
        #     if "상품" == name[:2]:
        #         product_dict['name'] = title
        #     else:
        #         product_dict['name'] = name
        # except NoSuchElementException as e:
        #     name = ''
        #     print("[ERROR] 상품명 추출 실패:",e)
        
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
            #print("[INFO] 할인 전 가격 없음")

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
        print(f"[ERROR] {product_code} 상품 기본 정보 추출 실패:",e)
        #driver.quit()
        return product_dict

# 상품 리뷰 추출
def get_product_review(driver, product_dict, page_divide):
    # 예외 발생 시 로깅을 위해 안전 초기화
    product_list = []
    product_code = product_dict.get('product_code', 'unknown')
    try:

        # 리뷰 추출
        if check_element_css("#sdpReview article", driver):
            container_id = "sdpReview"
        else:
            container_id = "btfTab"
        
        #sort_reviews_latest(driver)
        # 리뷰를 최신순으로 정렬렬
        try:
            review_btn = driver.find_elements(By.CSS_SELECTOR, 'div.review-order-container button')

            review_btn[1].click()
            time.sleep(random.uniform(2,3))
            product_code = product_dict['product_code']
            print(f"{product_code} 리뷰를 최신순으로 정렬했습니다.")
        except IndexError as e:
            print(f"[INFO] {product_code} 리뷰 정렬 버튼을 찾지 못했습니다.")
        
        #print("page number:"+str(page_divide))

        # 특정 상품 리뷰 분석 시 10 페이지 멀티프로세싱 진행
        if page_divide != -1:

            success_next_10_page = go_next_10_page(driver, page_divide, container_id)
            if not success_next_10_page:
                success_next_10_page = new_go_next_10_page(driver, page_divide)
            multi_run = False
        else:
            multi_run = True

        product_list = []
        total_review_count = 0
        # loop 횟수 제한
        max_loop = 2
        loop_cnt = 0
        # 여러 상품 추출인 경우 처음 부터 끝까지 추출 되도록 하기
        while (1):
            loop_cnt += 1
            for p in range(2,5):
                try:
                    articles = driver.find_elements(By.CSS_SELECTOR, f"#{container_id} article")

                    for article in articles:
                        review_dict = product_dict.copy()
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

                        # 도움된 사람 수 추출 및 리뷰 고유 ID
                        try:
                            review_help_cnt = article.find_element(By.CSS_SELECTOR, 'div.sdp-review__article__list__help').get_attribute("data-count")
                            review_unique_id = article.find_element(By.CSS_SELECTOR, 'div.sdp-review__article__list__help').get_attribute("data-review-id")
                        except NoSuchElementException:
                            review_help_cnt = 0


                        review_dict['product_code'] = product_code
                        review_dict['review_id'] = review_unique_id
                        review_dict['review_rating'] = review_rating
                        review_dict['review_date'] = review_date
                        review_dict['review_content'] = content
                        review_dict['review_keywords'] = keywords
                        review_dict['review_help_cnt'] = review_help_cnt
                        review_dict['crawled_at'] = _now_kst_iso()
                        
                        # 카프카에 리뷰 전송 (실패 시 에러 발생)
                        send_to_kafka_bridge(review_dict)
                        #product_list.append(review_dict)
                        #print(review_dict)
                        total_review_count += 1
                except NoSuchElementException as e:
                    print(f"[INFO] elements를 찾을 수 없음:", e)
                    continue

                original_next_page_success = go_next_page(driver, p+1, container_id)
                if not original_next_page_success:
                    next_page_success = click_next_review_page(driver, p+1)
                    if not next_page_success:
                        print("[INFO] 최신 방법으로 next_page_success가 False이므로 루프 종료")
                        break
            
            # multi_run이 False면 한 번만 실행하고 종료
            if not multi_run:
                #print("[INFO] multi_run이 False이므로 루프 종료")
                if page_divide == 0:
                    page = 1
                else:
                    page = page_divide * 10
                page_end = page + 9
                print(f"[INFO] {product_code} 리뷰 {page}~{page_end}페이지 추출 후 총 {total_review_count}개 완료했습니다.")
                break
            else:
                # multi_run이 True면 10페이지씩 넘기기 시도
                original_next_10_page_success = go_next_10_page(driver, 1, container_id)
                # 10페이지 넘기기 실패하면 예전 방법으로 시도 후 에도 실패하면 루프 종료
                if not original_next_10_page_success:
                    #print("[INFO] next_10_page_success가 False이므로 루프 종료")
                    next_10_page_success = new_go_next_10_page(driver, 1)
                    if not next_10_page_success:
                        print("[INFO] original_next_10_page_success가 False이므로 루프 종료")
                        break

            # 최대 반복횟수에 도달하면 루프 종료
            if max_loop <= loop_cnt:
                print("[INFO] 최대 루프 횟수에 도달하여 종료")
                break

        return total_review_count

    except Exception as e:
        print(f"[ERROR] {product_code} 리뷰 추출 실패 :", e)
        traceback.print_exc()
        return 0

# 쿠팡 리뷰 크롤링 파이프라인 
def coupang_crawling(args) -> int:
    driver = None
    product_code = 'unknown'
    print("[INFO] 쿠팡 리뷰 크롤링 시작")
    try:
        # page_divide 있으면
        if len(args) == 3:
            product_url, job_id, page_divide = args
        
        else:
            product_url, job_id = args
            page_divide = -1

        # 가상 디스플레이 시작, 프로세스 당 1개 생성
        with xvfb_display(width=1920, height=1080, depth=24) as disp:
            # 이제 DISPLAY가 설정됨. headless 불필요.
            driver = setup_driver()
            driver.get(product_url)
            time.sleep(random.uniform(4, 5))
            product_dict = get_product_info(driver)
            product_dict['job_id'] = job_id
            review_count = get_product_review(driver, product_dict, page_divide)
            product_code = product_dict['product_code']

            print("추출된 리뷰 개수:", review_count)
            print(f'[INFO] {product_code} 리뷰 추출을 완료했습니다.')
            return review_count


    except Exception as e:
        print(f"[ERROR] {product_code} 에러 발생 :", e)
        return 0
    finally:
        if driver:
            driver.quit()
        else:
            print("[INFO] driver is None")



if __name__ == "__main__":
    #url = "https://www.coupang.com/vp/products/6224605496?itemId=12196225924&vendorItemId=85326747347&sourceType=srp_product_ads&clickEventId=4745aa00-8150-11f0-8196-f228a66d645a&korePlacement=15&koreSubPlacement=1&clickEventId=4745aa00-8150-11f0-8196-f228a66d645a&korePlacement=15&koreSubPlacement=1"
    url ="https://www.coupang.com/vp/products/4548468621?itemId=13569079594&vendorItemId=80822526378&pickType=COU_PICK&q=%EC%B2%AD%EC%86%8C%EA%B8%B0&searchId=d78155d52759146&sourceType=search&itemsCount=36&searchRank=6&rank=6"
    args = [url, 'a123']
    start_xvfb()
    coupang_crawling(args)


