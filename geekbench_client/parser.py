from bs4 import BeautifulSoup
from collections import defaultdict
from typing import Callable, Any
import json

from .utils import *
from .parser_handlers.login_parse_handler import login_parse_handler
from .parser_handlers.cpu_parse_handler import cpu_parse_handler, latest_or_top_cpu_parse_handler, details_cpu_parse_handler
from .parser_handlers.gpu_parse_handler import gpu_parse_handler, latest_gpu_parse_handler
from .parser_handlers.ai_parse_handler import ai_parse_handler, latest_ai_parse_handler


class Parser:
    def __init__(self) -> None:
        self._data = defaultdict(lambda: defaultdict(dict))
        self._initialize_data_structure()

    # 데이터 구조화 초기화
    def _initialize_data_structure(self):
        self._data['all'] = defaultdict(dict)
        self._data['search'] = {
            'cpu': defaultdict(dict),
            'gpu': defaultdict(dict),
            'ai': defaultdict(dict),
        }
        self._data['details'] = {
            'cpu': defaultdict(dict),
            'gpu': defaultdict(dict),
        }
        self._data['latest'] = {
            'cpu': defaultdict(dict),
            'gpu': defaultdict(dict),
            'ai': defaultdict(dict),
        }
        self._data['top'] = {
            'single_cpu': defaultdict(dict),
            'multi_cpu': defaultdict(dict),
        }

    # 로그인 구문분석
    def login_parse(self, html:str):
        soup = BeautifulSoup(markup=html, features="lxml")
        (
        param, 
        token, 
        submit_name, 
        submit_value, 
        login_name, 
        passwrod_name
        ) = login_parse_handler(soup=soup)
        
        return (
            param, 
            token, 
            submit_name, 
            submit_value, 
            login_name, 
            passwrod_name
            )
    
    # cpu 구문분석 메인처리자
    def _cpu_parse_processor(self, html:str, parser:Callable[[str], Any]=None):
        soup = BeautifulSoup(markup=html, features="lxml")
        
        # 임시 사전 생성
        data_temp = defaultdict(dict)
        
        # 열(col) 개수만큼 반복합니다.
        for index, element in enumerate(
            soup.find_all(name="div", attrs={"class": "col-12 list-col"}),
            start=1
            ):
            
            (
            keys,
            values,
            url
            ) = parser(
                element=element,
                index=index
            )
                
            
            # 중복 방지를 위해 고유값인 url을 사용합니다.
            if url not in data_temp:                
                data_temp[url][keys[0]] = {"model name": values[0], "cpu info": values[1]}
                data_temp[url][keys[1]] = {"default date": values[2].strip(), "parsed date": extract_date(text=values[2])}
                data_temp[url][keys[2]] = values[3] # 플랫폼
                data_temp[url]["scores"] = {keys[3]: int(values[4]), keys[4]: int(values[5])}
                
        return data_temp

    # gpu 구문분석 메인처리자
    def _gpu_parse_processor(self, html:str, parser:Callable[[str], Any]=None):
        soup = BeautifulSoup(markup=html, features="lxml")
        
        # 임시 사전 생성
        data_temp = defaultdict(dict)
        
        # 열(col) 개수만큼 반복합니다.
        for index, element in enumerate(
            soup.find_all(name="div", attrs={"class": "col-12 list-col"}),
            start=1
            ):
            
            (
            keys,
            values,
            url
            ) = parser(
                element=element,
                index=index
            )
                
            
            # 중복 방지를 위해 고유값인 url을 사용합니다.
            if url not in data_temp:                
                data_temp[url][keys[0]] = {"model name": values[0], "cpu info": values[1]}
                data_temp[url][keys[1]] = {"default date": values[2].strip(), "parsed date": extract_date(text=values[2])}
                data_temp[url][keys[2]] = values[3] # 플랫폼
                data_temp[url][keys[3]] = values[4] # api 이름
                data_temp[url][keys[4]] = int(values[5])


        return data_temp


    # ai 구문분석 메인처리자
    def _ai_parse_processor(self, html:str, selection:bool) -> dict:
        soup = BeautifulSoup(markup=html, features="lxml")
        
        # 임시 사전 생성
        data_temp = defaultdict(dict)
        
        table = soup.find(name="table", attrs={"class": "table index-table"})
        tbody = table.find(name="tbody").find_all(name="tr") if table is not None else []

        # tr 개수만큼 반복합니다.
        for index, tr in enumerate(tbody, start=1):
            result = self._ai_parse_selection(soup=soup, tr=tr, index=index, data_temp=data_temp, selection=selection)
        return result
    

    def _ai_parse_selection(self, soup: str, tr: str, index: int, data_temp: dict, selection: bool):
        if selection:
            (
                cols,
                rows,
                url
            ) = ai_parse_handler(soup=soup, tr=tr, index=index)

        else:
            (
                cols,
                rows,
                url
            ) = latest_ai_parse_handler(soup=soup, tr=tr, index=index)

        return self._ai_write_selection(data_temp=data_temp, cols=cols, rows=rows, url=url, selection=selection)

    def _ai_write_selection(
                self,
                data_temp:dict=None,
                cols:tuple=None,
                rows:tuple=None,
                url:str=None,
                selection:bool=None
            ):
        
        # 중복 방지를 위해 고유값인 url을 사용합니다.
        if url not in data_temp:
            if selection:
                data_temp[url][cols[0]] = {"model name": rows[0], "model ap": rows[1]}
                data_temp[url][cols[1]] = rows[2]
                data_temp[url]["scores"] = {cols[2]: int(rows[3]),
                                            cols[3]: int(rows[4]), 
                                            cols[4]: int(rows[5])}
            else:
                data_temp[url][cols[0]] = {"default date": rows[0], "parsed date": parse_full_date(text=rows[0])}
                data_temp[url][cols[1]] = {"model name": rows[1], "model ap": rows[2]}
                data_temp[url][cols[2]] = rows[3]
                data_temp[url]["scores"] = {cols[3]: int(rows[4]),
                                            cols[4]: int(rows[5]), 
                                            cols[5]: int(rows[6])}
                
        return data_temp

            

    # cpu 부분 데이터 구문 분석
    def cpu_search_parse(self, html:str, page:str) -> dict:               
        # 데이터 추가
        self._add_data(
            page=page,
            data_name="GB6 CPU Search Results",
            all_data=self._data["all"],
            data=self._data["search"]["cpu"],
            data_temp=self._cpu_parse_processor(html=html, parser=cpu_parse_handler)
            )


    # gpu 부분 데이터 구문 분석
    def gpu_search_parse(self, html:str, page:str) -> dict:        
        # 데이터 추가
        self._add_data(
            page=page,
            data_name="GB6 GPU Search Results",
            all_data=self._data["all"],
            data=self._data["search"]["gpu"],
            data_temp=self._gpu_parse_processor(html=html, parser=gpu_parse_handler)
            )


    # ai 부분 데이터 구문 분석
    def ai_search_parse(self, html:str, page:str) -> dict:
        # 데이터 추가
        self._add_data(
            page=page,
            data_name="GB6 AI Search Results",
            all_data=self._data["all"],
            data=self._data["search"]["ai"],
            data_temp=self._ai_parse_processor(html=html, selection=True)
            )
    

    # 상세한 정보 구문분석
    # CPU 상세한
    def cpu_details_parse(self, url:str=None, html:set=None, result_data:dict=None, select_parse:bool=None):
        if select_parse:
            # 데이터 추가
            self._add_data(
                data_name="GB6 CPU DETAILS Results",
                all_data=self._data["all"],
                data=self._data["details"]["cpu"],
                data_temp=result_data,
                url=url
                )
        else:
            soup=BeautifulSoup(markup=html, features="lxml")
            details_cpu_parse_handler(soup=soup)

    # GPU 상세한
    def gpu_details_parse(self, url:str=None, html:set=None, result_data:dict=None, select_parse:bool=None):
        if select_parse:
            # 데이터 추가
            self._add_data(
                data_name="GB6 GPU DETAILS Results",
                all_data=self._data["all"],
                data=self._data["details"]["gpu"],
                data_temp=result_data,
                url=url
                )
        else:
            print("gpu parse 추가 필요")
            
    # 최신 CPU 데이터 반영 구문분석
    def latest_cpu_parse(self, html:str, page:str) -> None:       
        # 데이터 추가
        self._add_data(
            page=page,
            data_name="GB6 LATEST CPU Results",
            all_data=self._data["all"],
            data=self._data["latest"]["cpu"],
            data_temp=self._cpu_parse_processor(html=html, parser=latest_or_top_cpu_parse_handler)
            )

    # 최신 GPU 데이터 반영 구문분석
    def latest_gpu_parse(self, html:str, page:str) -> None:
        # 데이터 추가
        self._add_data(
            page=page,
            data_name="GB6 LATEST GPU Results",
            all_data=self._data["all"],
            data=self._data["latest"]["gpu"],
            data_temp=self._gpu_parse_processor(html=html, parser=latest_gpu_parse_handler)
            )

    # 최신 AI 데이터 반영 구문분석
    def latest_ai_parse(self, html:str, page:str) -> None:
        # 데이터 추가
        self._add_data(
            page=page,
            data_name="GB6 LATEST AI Results",
            all_data=self._data["all"],
            data=self._data["latest"]["ai"],
            data_temp=self._ai_parse_processor(html=html, selection=False)
            )

    # 가장 높은 싱글코어 데이터 구문분석
    def top_single_cpu_parse(self, html:str, page:str) -> None:
        # 데이터 추가
        self._add_data(
            page=page,
            data_name="GB6 TOP Single Results",
            all_data=self._data["all"],
            data=self._data["top"]["single_cpu"],
            data_temp=self._cpu_parse_processor(html=html)
            )

    # 가장 높은 멀티코어 데이터 구문분석
    def top_multi_cpu_parse(self, html:str, page:str) -> None:
        # 데이터 추가
        self._add_data(
            page=page,
            data_name="GB6 TOP Multi Results",
            all_data=self._data["all"],
            data=self._data["top"]["multi_cpu"],
            data_temp=self._cpu_parse_processor(html=html)
            )

    # 데이터 추가 함수
    def _add_data(self, page:int=None, data_name:str=None, all_data:dict=None, data:dict=None, data_temp:dict=None, url:str=None):

        # page 또는 url
        page_or_url = page if page is not None else url

        # 딕셔너리의 키 개수가 0개이면 빈 딕셔너리로 판단하여 추가하지 않음.
        if len(data_temp.keys()) != 0:
            # 모든 데이터 사전에 추가
            if page_or_url not in all_data[data_name]:
                all_data[data_name][page_or_url] = data_temp

            # 단일 데이터 사전에 추가
            if page_or_url not in data:
                data[page_or_url] = data_temp
                
    
    # 데이터를 체크합니다.
    def _emit_data_check(self, data:dict) -> dict:
        # return data if len(data.keys()) != 0 else None
        return json.dumps(data, ensure_ascii=False, indent=4) if len(data.keys()) != 0 else None


    # 데이터를 반환합니다.
    def emit_data(self, access_keys:list) -> dict:
        if isinstance(access_keys, list) and len(access_keys) >= 2:
            return self._emit_data_check(data=self._data[access_keys[0]][access_keys[1]]) # 각 키로 접근
            
        else:
            return self._emit_data_check(data=self._data[access_keys[0]])  # 단일 키로 접근