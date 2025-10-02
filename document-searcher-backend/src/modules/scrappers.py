from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timezone
import time, re, random, logging, subprocess

class Scrapper(ABC):
    # Currently not in use
    def __init__(self, arguments: list, experimentals: dict):
        self.opts = webdriver.ChromeOptions()
        self.service = webdriver.ChromeService(log_output=subprocess.DEVNULL)
        for arg in arguments:
            self.opts.add_argument(arg)
        for key, value in experimentals.items():
            self.opts.add_experimental_option(key, value)
        self.driver = webdriver.Chrome(options=self.opts, service=self.service)
        self.wait = WebDriverWait(self.driver, 30)

    def human_pause(self, a=0.8, b=1.8):
        time.sleep(random.uniform(a, b))

    def request_url(self, link: str, attempts=3):
        for i in range(1, attempts + 1):
            try:
                self.driver.get(link)
                return True
            except Exception as e:
                if i == attempts:
                    logging.warning(f"Giving up on {link}: {e}")
                    return False
                time.sleep(i)

    def quit(self):
        try:
            self.driver.quit()
        except Exception as e:
            logging.exception(e)

    @abstractmethod
    def scrappe_website(self):
        pass

class SinaleviScrapper(Scrapper):

    def __init__(self, arguments, experimentals):
        super().__init__(arguments, experimentals)

    def scrappe_website(self, query: str, pages: int):
        items = []
        try:
            main_url = "https://www.pgrweb.go.cr/SCIJ/main.aspx"
            main_collected = self.request_url(main_url, 3)

            if not main_collected:
                logging.error("Could not fetch main website, aborting...")
                return items
            
            # Attempts to load the query and do the search
            text_input = self.driver.find_element(By.ID, '_ctl0__ctl0_ContentPlaceHolder1_txtConsulta')
            text_input.send_keys(query)

            button_search = self.driver.find_element(By.ID, '_ctl0__ctl0_ContentPlaceHolder1_btnBuscar')
            button_search.click()

            urls = []
            current_page = 1
            current_link = 1

            while current_page <= pages:
                logging.info(f"Collecting links of page {current_page} of {pages}")
                links = self.wait.until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "a.text[href*='nrm_texto_completo.aspx']")
                    )
                )

                for a in links:
                    urls.append(a.get_attribute("href"))

                next_link = self.wait.until(
                        EC.element_to_be_clickable((By.ID, "_ctl0__ctl0_ContentPlaceHolder1_ContentPlaceHolderMenuBusqueda_Paginacion2_hlnkSiguiente"))
                    )
                next_link.click()
                self.wait.until(EC.staleness_of(links[0]))

                current_page += 1
                self.human_pause()

            for link in urls:
                try:
                    logging.info(f"Collecting content of {link}")
                    self.human_pause()
                    collected_url = self.request_url(link, 3)
                    if collected_url:
                        self.wait.until(EC.presence_of_element_located((By.ID, "dvContenedorTextoCompleto")))

                        body = self.driver.find_element(By.ID, "dvContenedorTextoCompleto").text
                        title = self.driver.find_element(
                            By.ID, "_ctl0__ctl0_ContentPlaceHolder1_ContentPlaceHolderMenuBusqueda_lblTitulo"
                        ).text

                        title = re.sub(r'[\\/:*?"<>|]+', "_", title).strip()[:150] or "documento"

                        items.append({
                            "id": current_link,
                            "name": title,
                            "content": body,
                            "url": link
                        })

                        current_link += 1
                except Exception as e:
                    logging.warning(f"Error on previous link, skipping")
        except Exception as e:
            print(f"Error trying to scrappe website, aborting...")
        
        return items
    
class NexusScrapper(Scrapper):

    def __init__(self, arguments, experimentals):
        super().__init__(arguments, experimentals)

    def scrappe_website(self, query: str, pages: int):
        result = ""
        main_url = f"https://nexuspj.poder-judicial.go.cr/search?nq=&q={query}"
        main_collected = self.request_url(main_url, 3)

        if not main_collected:
            logging.error("Could not fetch main website, aborting...")
            return
        
        LINKS_CSS = "a[ng-click*='showDetail']"
        
        self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, LINKS_CSS)))
        count = len(self.driver.find_elements(By.CSS_SELECTOR, LINKS_CSS))
        print(f"Number of links {count}")

if __name__ == "__main__":
    arguments = [
        "--no-sandbox",
        "--headless=new",
        "--disable-gpu",
        "--window-size=1365,768",
        "--lang=es-CR",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36",
        "--disable-blink-features=AutomationControlled",
    ]

    experimentals = {
        "excludeSwitches": ["enable-automation"],
        "useAutomationExtension": False,
    }
    nexus = NexusScrapper(arguments, experimentals)
    nexus.scrappe_website('capital',1)