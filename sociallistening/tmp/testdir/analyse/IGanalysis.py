import csv
import datetime
import json
import time
import os

import requests

# Business AccountのIDの入力．
# 注意：（me?fields=id,name）で出てきたものではない．忘れた場合は，
# https://accountscenter.instagram.com/profiles/
# でビジネスアカウントを選択すればURL欄に出てくる．
IG_USER_ID = "17841471031204341" 
LONG_ACCESS_TOKEN = "EAAKqm7QNvOABOyW2WyJQInZAHuA7tdu5JVctxepCfVD3BRcA0VEvzwXYQyY4GJjLo8KbZA8YMlxUNAbkIqJNWoVKMOOP7todVOkxYF6Dg2uXbGfzs1zrL2DrX1XbjZBiZAPHZBrMZB1itsd8iT7sdQDD6m14WScZAVYIeEodHrNbDznLNmjI9ZBzUbr2OH6GmMiQlImo" 
# 一応短期トークンを使いたいなら↓のLONG_ACCESS_TOKENを書き換えて．

APP_INFO = {
    "INSTAGRAM_APP_NAME" : "Instagram",
    "API_VERSION": "v23.0"
    }


ACCESS_TOKEN_TEST = LONG_ACCESS_TOKEN

URL_GRAPH_API_ROOT = "https://graph.facebook.com/" + APP_INFO["API_VERSION"] + "/"
BASEURL_GET_HASHTAG_ID_BY_NAME = URL_GRAPH_API_ROOT + "ig_hashtag_search?"


# 投稿に関する欲しいfieldを入力しておく．
WANTED_FIELDS_LIST_BASE = ["id", "timestamp", "permalink", "media_product_type", "media_type", "comments_count", "caption"]

# URLの組み立て．

def make_url_get_hashtag_id_by_name(
        hashtag_name, user_id=IG_USER_ID, access_token=ACCESS_TOKEN_TEST):
    
    url = BASEURL_GET_HASHTAG_ID_BY_NAME + "user_id=" + user_id 
    url = url + "&access_token=" + access_token + "&q=" + hashtag_name
    return url
 

def make_url_get_posts_by_hashtag_id(
        hashtag_id, recent_or_top="recent", after=None, fields_list=WANTED_FIELDS_LIST_BASE, 
        user_id=IG_USER_ID, access_token=ACCESS_TOKEN_TEST):

    fields_str = str(",".join(fields_list))
    print(fields_str)

    request_url = URL_GRAPH_API_ROOT + hashtag_id
    if recent_or_top == "top":
        request_url = request_url + "/top_media?"
    elif recent_or_top == "recent":
        request_url = request_url + "/recent_media?"
    else:
        # どちらでもなかったらとりあえずrecentで取る．
        request_url = request_url + "/recent_media?"
    request_url = request_url + f"user_id={user_id}&access_token={access_token}&fields={fields_str}"
    
    if after is not None:
        request_url = request_url + f"&after={str(after)}"

    result = request_url
    
    return result

# ハッシュタグIDの取得．
def get_hashtag_id_by_name(hashtag_name, user_id=IG_USER_ID, access_token=ACCESS_TOKEN_TEST):
    
    url = make_url_get_hashtag_id_by_name(hashtag_name=hashtag_name,
        user_id=user_id, access_token=access_token)
    print(url)
    response = requests.get(url)
    res_text = json.loads(response.text)
    print(res_text)
    
    if "error" in res_text.keys():
        print("response error")
        return None
    
    result = json.loads(response.text)["data"][0]["id"]
    result = str(result)
    print(result)

    return result

# 投稿の取得（ページネーション対応）．
def get_posts_by_hashtag_id_with_paging(
        hashtag_id, max_paging=7, recent_or_top="recent", 
        fields_list=WANTED_FIELDS_LIST_BASE, user_id=IG_USER_ID, 
        access_token=ACCESS_TOKEN_TEST):

    notice = "ページネーション対応でpost取得。"
    print(notice)

    now_paging = 0
    cursors_after = None
    will_continue = True
    
    posts_list = []

    while will_continue:
    
        url = make_url_get_posts_by_hashtag_id(
            hashtag_id=hashtag_id, recent_or_top=recent_or_top, 
            after=cursors_after, fields_list=fields_list, 
            user_id=user_id, access_token=access_token
            )
        print(url)
        response = requests.get(url)
        print(response)
        res_text = json.loads(response.text)

        if "error" in res_text.keys():
            print("Error.")
            print(response.headers)
            print(res_text)
            if cursors_after is not None:
                print("cursors_after: " + str(cursors_after))
            print(f"{hashtag_id} : Please check the error message. " + 
                  "If (#4) ('Application request limit reached'), please try again after a while.")
            break

        cursors_after = None

        if "paging" in res_text.keys():
            if "cursors" in res_text["paging"].keys():
                cursors = res_text["paging"]["cursors"]
                if "after" in cursors.keys():
                    cursors_after = cursors["after"]
        if cursors_after is None:
            will_continue = False
        if now_paging >= max_paging:
            will_continue = False
        
        try:
            if "data" in res_text.keys():
                posts_list.extend(res_text["data"])
        except Exception as e:
            print(e)
            print(f"{hashtag_id} : The data is not good.")
            break
        
        now_paging = now_paging + 1

        time.sleep(2)
    
    return posts_list

def get_api_response_header(access_token):

    url = URL_GRAPH_API_ROOT +  "me?fields=id,name&access_token=" + access_token
    response = requests.get(url)
    print(response.headers)

    return str(response.headers)


def is_limit_reached(access_token):

    result = get_api_response_header(access_token=access_token)
    if "(#4) Application request limit reached" in result:
        return True
    else:
        return False

def make_json_from_posts_list_ymd(label: str, posts_list: list, will_save_ascii: bool = False):

    today = datetime.date.today()
    filename = label + '_' + today.strftime('%Y%m%d_%H') + '.json'
    make_json_from_list(filename=filename, ls=posts_list, will_save_ascii=will_save_ascii)

    return True


def make_json_from_list(filename: str, ls: list, data_dir: str = "./", will_save_ascii: bool = False):

    notice = "指定filenameで、指定listをjsonとして保存。"
    print(notice)

    if not filename.endswith('.json'):
        filename = filename + ".json"
    
    file_path = os.path.join(data_dir, filename)

    with open(file_path, 'w',encoding="utf-8") as f:
        json.dump(ls, f, indent=2, ensure_ascii=False)
    
    if will_save_ascii:
        print("ensure_asciiも保存")
        filename_ascii = "ascii_" + filename
        file_path_ascii = os.path.join(data_dir, filename_ascii)
        with open(file_path_ascii, 'w',encoding="utf-8") as f:
            json.dump(ls, f, indent=2, ensure_ascii=True)

    return ls

def get_posts_by_hashtag_name_with_paging(
        hashtag_name, max_paging=7, recent_or_top="recent", 
        fields_list=WANTED_FIELDS_LIST_BASE, user_id=IG_USER_ID, access_token=ACCESS_TOKEN_TEST):
    
    hashtag_id = get_hashtag_id_by_name(
        hashtag_name=hashtag_name, user_id=user_id, access_token=access_token)
    
    posts_list = get_posts_by_hashtag_id_with_paging(
        hashtag_id=hashtag_id, max_paging=max_paging, 
        recent_or_top=recent_or_top, fields_list=fields_list, 
        user_id=user_id, access_token=access_token)

    return posts_list


def make_json_by_hashtag_name_with_paging(
        hashtag_name, max_paging=7, recent_or_top="recent", 
        fields_list=WANTED_FIELDS_LIST_BASE, will_save_ascii=True, 
        user_id=IG_USER_ID, access_token=ACCESS_TOKEN_TEST):

    posts_list = get_posts_by_hashtag_name_with_paging(
        hashtag_name=hashtag_name, max_paging=max_paging, 
        recent_or_top=recent_or_top, fields_list=fields_list, 
        user_id=user_id, access_token=access_token)
    
    label = "IG_tag_" + hashtag_name + "_pmax_" + str(max_paging) + "_" + recent_or_top

    make_json_from_posts_list_ymd(label=label, posts_list=posts_list, will_save_ascii=will_save_ascii)

    return posts_list

def main():

    access_token = LONG_ACCESS_TOKEN

    hashtag_names_for_recent = []
    hashtag_names_for_top = ['ハンバーグ']

    for hashtag_name in hashtag_names_for_recent:
        now_info = make_json_by_hashtag_name_with_paging(hashtag_name=hashtag_name, 
                                        max_paging=8, recent_or_top="recent", 
                                        will_save_ascii=False,
                                        user_id=IG_USER_ID, access_token=access_token)
        if now_info is None:
            with open("error.csv", mode="a", newline="") as error_file:
                error_writer = csv.writer(error_file)
                error_writer.writerow([datetime.datetime.now(), hashtag_name, "繰り返しでエラー(recent)"])
            if is_limit_reached(access_token=access_token):
                break
            else:
                pass
        time.sleep(5)

    for hashtag_name in hashtag_names_for_top:
        now_info = make_json_by_hashtag_name_with_paging(hashtag_name=hashtag_name, 
                                        max_paging=8, recent_or_top="top", 
                                        will_save_ascii=False,
                                        user_id=IG_USER_ID, access_token=access_token)
        if now_info is None:
            with open("error.csv", mode="a", newline="") as error_file:
                error_writer = csv.writer(error_file)
                error_writer.writerow([datetime.datetime.now(), hashtag_name, "繰り返しでエラー(top)"])
            if is_limit_reached(access_token=access_token):
                break
            else:
                pass
        time.sleep(5)

    return True

if __name__ == "__main__":

    main()

