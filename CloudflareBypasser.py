import time
from DrissionPage import ChromiumPage

class PageDisconnectedError(Exception):
    """Custom exception for when the browser page disconnects."""
    pass

class CloudflareBypasser:
    def __init__(self, driver: ChromiumPage, max_retries=-1, log=True):
        self.driver = driver
        self.max_retries = max_retries
        self.log = log

    def search_recursively_shadow_root_with_iframe(self,ele):
        if ele.shadow_root:
            if ele.shadow_root.child().tag == "iframe":
                return ele.shadow_root.child()
        else:
            for child in ele.children():
                result = self.search_recursively_shadow_root_with_iframe(child)
                if result:
                    return result
        return None

    def search_recursively_shadow_root_with_cf_input(self,ele):
        if ele.shadow_root:
            if ele.shadow_root.ele("tag:input"):
                return ele.shadow_root.ele("tag:input")
        else:
            for child in ele.children():
                result = self.search_recursively_shadow_root_with_cf_input(child)
                if result:
                    return result
        return None
    
    def locate_cf_button(self):
        button = None
        # Basic search for the button
        try:
            eles = self.driver.eles("tag:input[name*=turnstile][type=hidden]")
            if eles:
                parent = eles[0].parent()
                if parent and parent.shadow_root:
                    child = parent.shadow_root.child()
                    # The child is the iframe
                    if child:
                        body = child('tag:body')
                        if body and body.shadow_root:
                            button = body.shadow_root('tag:input')
        except Exception as e:
            self.log_message(f"Error in basic search for CF button: {e}")
            if "与页面的连接已断开" in str(e) or "Connection to the page was disconnected" in str(e):
                raise PageDisconnectedError("Page disconnected during basic search")

        if button:
            return button

        # Recursive search if basic search fails
        self.log_message("Basic search failed. Searching for button recursively.")
        try:
            body_ele = self.driver.ele("tag:body")
            if not body_ele:
                self.log_message("Body element not found for recursive search.")
                return None
                
            iframe = self.search_recursively_shadow_root_with_iframe(body_ele)
            if iframe:
                iframe_body = iframe("tag:body")
                if iframe_body:
                    button = self.search_recursively_shadow_root_with_cf_input(iframe_body)
        except Exception as e:
            self.log_message(f"Error in recursive search for CF button: {e}")
            if "与页面的连接已断开" in str(e) or "Connection to the page was disconnected" in str(e):
                raise PageDisconnectedError("Page disconnected during recursive search")

        return button

    def log_message(self, message):
        if self.log:
            print(message)

    def click_verification_button(self):
        try:
            button = self.locate_cf_button()
            if button:
                self.log_message("Verification button found. Attempting to click.")
                button.click()
            else:
                self.log_message("Verification button not found.")
        except PageDisconnectedError:
            raise  # Re-raise the specific error to be caught by bypass()
        except Exception as e:
            self.log_message(f"Error clicking verification button: {e}")
            if "与页面的连接已断开" in str(e) or "Connection to the page was disconnected" in str(e):
                raise PageDisconnectedError("Page disconnected during click")

    def is_bypassed(self):
        try:
            title = self.driver.title.lower()
            return "just a moment" not in title
        except Exception as e:
            self.log_message(f"Error checking page title: {e}")
            return False

    def bypass(self):
        
        try_count = 0

        while not self.is_bypassed():
            if 0 < self.max_retries + 1 <= try_count:
                self.log_message("Exceeded maximum retries. Bypass failed.")
                break

            try:
                self.log_message(f"Attempt {try_count + 1}: Verification page detected. Trying to bypass...")
                self.click_verification_button()

            except PageDisconnectedError as e:
                self.log_message(f"Handled a page disconnect: {e}. Waiting for page to stabilize.")
                time.sleep(5)  # Wait for the page to reload/stabilize
                continue  # Retry the loop without incrementing try_count

            try_count += 1
            time.sleep(2)

        if self.is_bypassed():
            self.log_message("Bypass successful.")
        else:
            self.log_message("Bypass failed.")
