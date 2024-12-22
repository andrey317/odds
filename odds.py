import requests
import matplotlib.pyplot as plt
from apython import  load_json, dumpjson
from datetime import datetime, timedelta
import numpy as np


lb_pages = 2           # 2*10
end_january_day = 15   # 2025.01.15

def parse_leaderboard(count_pages):
    result = []
    for i in range(count_pages):
        url = f"https://www.oddsgarden.io/api/soft-staking/leaderboard?collection_address=stars1vjxr6hlkjkh0z5u9cnktftdqe8trhu4agcc0p7my4pejfffdsl5sd442c7&page={i}"
        resp = requests.get(url).json()
        result.extend(resp["data"])
    return result
# {
#   "message": "Get leaderboard successfully",
#   "data": [
#     {
#       "collection_address": "stars1vjxr6hlkjkh0z5u9cnktftdqe8trhu4agcc0p7my4pejfffdsl5sd442c7",
#       "staker_address": "stars1d7sw0t3nyajddyjtvwargqkypqx0yumdarq302",
#       "staker_nft_staked": 23,
#       "user_image_url": "https://ipfs-gw.stargaze-apis.com/ipfs/bafybeif7j4jrvmafknh7v3n73v5f56gkrud37rhg3gdux5o7rbg6o3fxaq/1065.png",
#       "total_points": "370",
#       "ranking": "21"
#     },

def parse_stargaze():
    GRAPHQL_ENDPOINT = "https://graphql.mainnet.stargaze-apis.com/graphql"
    HEADERS = {
        "Content-Type": "application/json"
    }
    QUERY = """
    query Query(
      $tokensOffset: Int
    ) {
      tokens(    
        offset: $tokensOffset
        limit: 100
        collectionAddr: "stars1vjxr6hlkjkh0z5u9cnktftdqe8trhu4agcc0p7my4pejfffdsl5sd442c7"
      ) {
        tokens {
          name
          owner {
            address
          }
          traits {
            name
            value
          }
        }
        pageInfo {
          offset
          total
          limit
        }
      }
    }
    """
    print("parsing stargaze -> 5000")
    offset = 0
    all_tokens = []
    while True:
        payload = {
            "query": QUERY,
            "variables": {"tokensOffset": offset}
        }

        response = requests.post(GRAPHQL_ENDPOINT, json=payload, headers=HEADERS)
        response.raise_for_status()

        data = response.json()
        if "errors" in data:
            raise Exception(f"GraphQL Errors: {data['errors']}")

        root = data["data"]["tokens"]
        #page_info = root["pageInfo"]
        tokens = root["tokens"]
        if len(tokens) == 0:
            break
        print("\b\b\b\b\b", offset, end="")
        offset += len(tokens)
        all_tokens.extend(tokens)
    print("\b\b\b\b\b")
    return all_tokens


def process_data(sg_data):
    weight_gold = 10
    weight_silv = 8
    weight_bron = 5

    aggr = {}
    for i in sg_data:
        owner = i["owner"]["address"]
        tier = [i["value"] for i in i["traits"] if i["name"] == 'Tier'][0]

        if not (x := aggr.get(owner)):
            x = aggr[owner] = {"total": 0, "Gold": 0, "Silver": 0, "Bronze": 0}

        x[tier] += 1
        x["total"] = x["Gold"] * weight_gold + x["Silver"] * weight_silv + x["Bronze"] * weight_bron

    print("top gainers")
    a = sorted(aggr.items(), key=lambda x: x[1]["total"], reverse=True)
    for ln, (addr, i) in enumerate(list(a)[:lb_pages*10]):
        g = i["Gold"]
        s = i["Silver"]
        b = i["Bronze"]
        wzrd = i["total"]
        print(f"#{ln + 1:02} {addr}\t{wzrd:5} wzrd/d   {(g + s + b):3} nft      {g:3} g  {s:3} s  {b:3} b")

    return aggr

def graph(board, aggr):
    lines = len(board)
    date1 = datetime.now()
    date2 = datetime(2025, 1, end_january_day)

    days = (date2-date1).days
    x_values = range(days)
    dates = [date1 + timedelta(days=i) for i in range(days)]

    plt.figure(figsize=(12, 8))
    colormap = plt.get_cmap(f'tab{lines}')


    y_values = []
    for i in range(lines):
        lb = board[i]
        addr = lb["staker_address"]
        addr_strip = addr[5:9] + '...' + addr[-4:]
        y0 = int(lb["total_points"])
        if ag:=aggr.get(addr):
            k = ag["total"]
        else:
            k = 0
        y_values.append( [y0 + k * x for x in x_values] )  # y = n * x for n in 1 to 20

        plt.text(dates[-1], y_values[i][-1], f'#{i + 1:02}', color=colormap(i / lines), va='bottom')
        plt.plot(dates, y_values[i], label=f'#{i + 1:02} {addr_strip}', color=colormap(i / lines))

    plt.grid(which='both', linestyle='--', linewidth=0.5, alpha=0.7)

    plt.xticks(ticks=dates, labels=[date.strftime('%Y-%m-%d') for date in dates], rotation=90)
    max_y = max(max(y_values))
    plt.yticks(ticks=np.arange(0, max_y + 1000, 1000))
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1), ncol=1)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    try:
        board = parse_leaderboard(lb_pages)
        #dumpjson("leaderboard.json", board)

        sg_data = parse_stargaze()
        #dumpjson("sg_data.json", sg_data)

        #sg_data = load_json("sg_data.json")
        aggr = process_data(sg_data)



    except Exception as e:
        print(f"An error occurred: {e}")

    graph(board, aggr)

