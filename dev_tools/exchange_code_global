import requests
import re
from datetime import datetime, timedelta

class GameRedeemCode:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def get_post_id(self):
        """获取活动ID"""
        url = f"https://bbs-api-os.hoyolab.com/community/post/wapi/getNewsList?gids=6&page_size=15&type=3"
        print(url)
        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()

            if data.get("retcode") != 0:
                return False

            for post in data["data"]["list"]:
                content = post.get("post", {}).get("multi_language_info", {}).get("lang_subject", "").get("zh-cn", "")
                match = re.search(r'act_id=([^\\]+)', content)
                if "前瞻" in content:
                    self.post_id = post.get("post", {}).get("post_id")
                    return True
            return False
        except Exception as e:
            print(f"获取post_id失败: {str(e)}")
            return False

    def get_redeem_codes(self):
        """获取兑换码列表"""
        if not self.get_post_id():
            return None

        # live_info = self.get_live_info()
        # if not live_info or live_info["remain"] > 0:
        #     return None

        url = f"https://bbs-api-os.hoyolab.com/community/post/wapi/getPostFull?post_id={self.post_id}"
        # headers = {**self.headers, "x-rpc-act_id": self.act_id}
        print(url)
        # print(headers)
        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()
            content = data.get("data", {}).get("post", {}).get("post", {}).get("content", "")
            code = re.findall(r'https://hsr\.hoyoverse\.com/gift\?code=([A-Z0-9]+)\"', content)
            return code
        except Exception as e:
            print(f"获取兑换码失败: {str(e)}")
            return None

    def format_result(self):
        """格式化输出结果"""
        codes = self.get_redeem_codes()
        if not codes:
            return "当前没有可用的兑换码"

        return (
                "🎮 兑换码列表：\n" +
                "\n".join([f"▸ {code}" for code in codes])
        )


# 使用示例
if __name__ == "__main__":
    game = GameRedeemCode()

    result = game.format_result()
    print(result)




