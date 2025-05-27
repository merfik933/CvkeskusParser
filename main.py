import utils.config_util as config_util
import utils.df_util as df_util
import utils.helper as hp

import utils.requests_manager as rm

import time

def start(main_dir, start_with_page=1):
    print("Starting cvkeskusParser...")

    url, xlsx_file_name, xlsx_sheet_name, save_file_interval = config_util.get_all("cvkeskus", main_dir)
    save_file_interval = int(save_file_interval)

    columns = ["Vacancy Name", "Company Name", "Salary", "Location", "Published Date", "End Date", "Type of job", "EMail", "Phone"]
    df = df_util.create_df(columns)

    page_size = 25
    start_with_element = (start_with_page - 1) * page_size
    url = hp.update_url_param(url, "start", start_with_element)

    progress_counter = start_with_element
    while True:
        page = rm.get_page(url)

        results = rm.get_elements(page, "section article")

        for result in results:
            start_time = time.time()

            vacancy_name = rm.get_text(result, "h2")
            company_name = rm.get_text(result, ".job-company")
            salary = rm.get_text(result, ".salary-block")
            location = rm.get_text(result, "span:has(span.location)")

            vacancy_url = "https://www.cvkeskus.ee/" + rm.get_attribute(result, "href", "a.jobad-url")

            vacancy_page = rm.get_page(vacancy_url)

            keys_1 = ["Kuulutus sisestati", "Aegub", "Töö tüüp"]
            published_date_1, end_date_1, type_of_job_1 = rm.find_values_by_keys_in_box(vacancy_page, ".flex-col.mt-6 div > div > div:first-child", ".flex-col.mt-6 div > div > div:last-child", keys_1, None)

            keys_2 = ["Published", "Expires", "Job type"]
            published_date_2, end_date_2, type_of_job_2 = rm.find_values_by_keys_in_box(vacancy_page, ".flex-col.mt-6 div > div > div:first-child", ".flex-col.mt-6 div > div > div:last-child", keys_2, None)

            keys_3 = ["Добавлено", "Заканчивается", "Вид работы"]
            published_date_3, end_date_3, type_of_job_3 = rm.find_values_by_keys_in_box(vacancy_page, ".flex-col.mt-6 div > div > div:first-child", ".flex-col.mt-6 div > div > div:last-child", keys_3, None)

            published_date = published_date_1 or published_date_2 or published_date_3
            end_date = end_date_1 or end_date_2 or end_date_3
            type_of_job = type_of_job_1 or type_of_job_2 or type_of_job_3

            main = rm.get_element(vacancy_page, "header + div")

            emails = rm.get_elements(main, "a[href^='mailto:']")
            email = ", ".join([email["href"].replace("mailto:", "") for email in emails]).strip()

            phones = rm.get_elements(main, "a[href^='tel:']")
            phone = ", ".join([phone["href"].replace("tel:", "") for phone in phones]).strip()

            row = {
                "Vacancy Name": vacancy_name,
                "Company Name": company_name,
                "Salary": salary,
                "Location": location,
                "Published Date": published_date,
                "End Date": end_date,
                "Type of job": type_of_job,
                "EMail": email,
                "Phone": phone
            }
            df = df_util.add_row(df, row)

            progress_counter += 1
            if progress_counter % save_file_interval == 0:
                df_util.save_df(df, main_dir, xlsx_file_name, xlsx_sheet_name)

            end_time = time.time()
            elapsed_time = end_time - start_time
            if elapsed_time < 1:
                time.sleep(1 - elapsed_time)
                elapsed_time = 1
            print(f"{company_name} data parsed in {(elapsed_time):.2f} seconds. [{progress_counter}]")

            vacancy_name = ""
            company_name = ""
            salary = ""
            location = ""
            published_date = ""
            end_date = ""
            type_of_job = ""
            email = ""
            phone = ""

        next_page = rm.get_element(page, "li a:has(.chevron-right)", None)
        if not next_page:
            break
        url = hp.update_url_param(url, "start", progress_counter)

    df_util.save_df(df, main_dir, xlsx_file_name, xlsx_sheet_name)

    print(f"Data parsing completed. {progress_counter} companies parsed.")

if __name__ == "__main__":
    import os

    current_dir = os.path.dirname(os.path.realpath(__file__))

    start(current_dir)