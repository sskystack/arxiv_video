
import matplotlib.pyplot as plt
from pyecharts.charts import Line
from pyecharts import options as opts
import pandas as pd
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot as driver
from cfg.safe_session import session_factory, use_session


from cfg.STATUS import *
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
from matplotlib.cm import get_cmap





#
# @use_session()
# def process_paper_cluser_ID(lpqa_paper, session=None):
#     lpqa_paper = session.query(Papers).filter(Papers.external_id == lpqa_paper.external_id).first()
#
#     kwds = [item.strip() for item in lpqa_paper.paper_detail.gpt_kwds.split(',')][:3]
#     id_array = infer_BIRCH_from_scratch(kwds)
#     id_array = np.array([x for x in id_array.flatten() if x is not None])
#
#     cluster_id = int(id_array.min())
#     lpqa_paper.paper_detail.cluster_id = cluster_id
#     lpqa_paper.valid = TaskStatus.TO_SCRIPT_GENERATION
# def update_kwd_cluster_ID(date=None):
#     cur_day_papers = current_day_data(ID=TaskStatus.TO_CLUSTER, date=date)
#
#     with ThreadPoolExecutor(max_workers=8) as executor:
#         futures = [executor.submit(process_paper_cluser_ID, paper) for paper in cur_day_papers]
#
#         for future in futures:
#             future.result()  # 捕获线程内部异常
#
#
#
# def render_world_map():
#     papers = current_day_data(ID=None)
#     update_cur_day_country(papers)
#     country_dict = get_country_pub_num_dict()
#     print(country_dict)
#     make_snapshot(driver, map_chart(country_dict).render(), "world_map.png")



if __name__ == '__main__':
    # render_weekly_kwd_trends()
    #
    # render_word_cloud()
    # update_kwd_cluster_ID(date=datetime.datetime(2024, 12, 25))
    # render_world_map()
    # print(infer_BIRCH_from_scratch('Vision-language model,Label Propagation,Zero-shot Learning'.split(',')))
    update_kwd_cluster_ID(date=None)