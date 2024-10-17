import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json

from apps.manager.progress_bar import ProgressBar

class TagPriorityGenerator:
    def __init__(self, api_key, model="text-embedding-ada-002"):
        """
        OpenAI API를 사용하여 임베딩을 생성하고 태그 순위를 매기는 클래스

        :param api_key: OpenAI API 키
        :param model: 임베딩 모델 (기본값: 'text-embedding-ada-002')
        """
        openai.api_key = api_key
        self.model = model

    def get_embedding(self, text):
        """OpenAI 임베딩 모델을 사용하여 텍스트 임베딩을 생성"""
        response = openai.Embedding.create(input=[text], model=self.model)
        embedding = response['data'][0]['embedding']
        return np.array(embedding)

    def generate_tag_embeddings(self, tags):
        """
        각 태그 설명에 대해 임베딩을 생성
        :param tags: 태그 설명이 담긴 딕셔너리 {태그 이름: 설명}
        :return: 태그 임베딩 딕셔너리 {태그 이름: 임베딩 벡터}
        """
        tag_embeddings = {}
        for tag, description in tags.items():
            tag_embeddings[tag] = self.get_embedding(description)
        return tag_embeddings

    def calculate_similarity(self, scenario_embedding, tag_embeddings):
        """
        시나리오 임베딩과 태그 임베딩 간의 코사인 유사도를 계산하여 priority 값을 생성
        :param scenario_embedding: 시나리오의 임베딩 벡터
        :param tag_embeddings: 태그 임베딩 딕셔너리 {태그 이름: 임베딩 벡터}
        :return: 각 태그에 대한 유사도 기반 priority {태그 이름: priority 값}
        """
        similarities = {}
        for tag, embedding in tag_embeddings.items():
            similarity = cosine_similarity([scenario_embedding], [embedding])[0][0]
            similarities[tag] = similarity
        return similarities

    def assign_priority(self, similarities):
        """
        유사도를 기반으로 priority 순서를 매김
        :param similarities: 태그별 유사도 딕셔너리
        :return: 태그별 priority 딕셔너리
        """
        # 유사도를 기준으로 높은 순서대로 태그 정렬
        sorted_tags = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
        
        # priority를 유사도가 높은 순서대로 1, 2, 3, ... 할당
        priority_map = {tag: rank + 1 for rank, (tag, similarity) in enumerate(sorted_tags)}
        
        return priority_map

    def calculate_tag_ranking(self, tag_embeddings):
        """
        태그들 간의 코사인 유사도를 계산하여 순위를 생성
        :param tag_embeddings: 태그 임베딩 딕셔너리 {태그 이름: 임베딩 벡터}
        :return: 각 태그에 대한 유사도 기반 순위 {태그 이름: 유사한 태그 순위}
        """
        tag_names = list(tag_embeddings.keys())
        embeddings = np.array(list(tag_embeddings.values()))
        similarities = cosine_similarity(embeddings)

        # 유사도 결과를 저장할 딕셔너리
        similarity_ranking = {}

        for i, tag in enumerate(tag_names):
            # 각 태그의 다른 태그와의 유사도를 정렬하여 순위 매기기
            similar_tags = sorted(
                [(tag_names[j], similarities[i][j]) for j in range(len(tag_names)) if i != j],
                key=lambda x: x[1], reverse=True
            )

            # 상위 유사한 태그 3개를 선택하여 우선순위로 설정
            similarity_ranking[tag] = {
                f"{rank + 1}": similar_tags[rank][0]
                for rank in range(min(3, len(similar_tags)))
            }

        return similarity_ranking

    def generate_priority_data(self, scenario, tags):
        """
        시나리오를 기반으로 태그의 우선순위 데이터를 생성
        :param scenario: 시나리오 설명 텍스트
        :param tags: 태그 설명 딕셔너리
        :return: 우선순위 데이터를 담은 딕셔너리
        """
        progress_bar = ProgressBar.get_instance()
        progress_bar.set_now_log('시나리오를 기반으로 태그의 우선순위 데이터를 생성')
        progress_bar.start_progress(6)
        # 시나리오 임베딩 생성
        scenario_embedding = self.get_embedding(scenario)
        progress_bar.done_1_task()
        
        # 각 태그 설명에 대해 임베딩 생성
        tag_embeddings = self.generate_tag_embeddings(tags)
        progress_bar.done_1_task()
        
        # 시나리오와 각 태그 설명 간의 유사도 기반 priority 계산
        tag_priorities = self.calculate_similarity(scenario_embedding, tag_embeddings)
        progress_bar.done_1_task()

        # 유사도 기반 priority를 정렬 순서로 변경
        tag_priorities = self.assign_priority(tag_priorities)
        progress_bar.done_1_task()

        # 태그들 간의 유사도 기반 순위 계산
        tag_ranking = self.calculate_tag_ranking(tag_embeddings)
        progress_bar.done_1_task()

        # 태그 순위와 설명을 결합하여 JSON 형식으로 변환
        tag_priority_data = {}
        for tag, description in tags.items():
            tag_priority_data[tag] = {
                "priority": tag_priorities[tag],  # 시나리오와 유사도 기반 priority
                "tag_ranking": tag_ranking.get(tag, {}),  # 태그 간 유사도 순위
                "description": description
            }
        progress_bar.done_1_task()

        return tag_priority_data

    def save_priority_data(self, scenario, tags, output_path="tag_priority_data.json"):
        """
        태그 우선순위 데이터를 생성하고 저장
        :param scenario: 시나리오 텍스트
        :param tags: 태그 설명 딕셔너리
        :param output_path: 우선순위 데이터를 저장할 파일 경로
        """
        tag_priority_data = self.generate_priority_data(scenario, tags)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tag_priority_data, f, indent=4, ensure_ascii=False)

        print(f"유사도 기반 태그 순위가 '{output_path}'에 저장되었습니다.")