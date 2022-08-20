$(document).ready(function(){
	// 로그아웃 버튼
	$(document).on("click", ".logout", function(){
		location.href = "./index.html";
	});
	
	// 취소버튼
	$(document).on("click", ".btn-cancel", function(){
		history.back();
		return false;
	});
	
	// 강의만들기 이동
	$(document).on("click", ".lectureInfoAddBtnDiv", function(){
		location.href = $(this).attr("link");
	});
	
	// 과제목록 이동
	$(document).on("click", ".lectureInfoDiv", function(){
		location.href = $(this).attr("link");
	});
	
	// 과제목록 상세보기
	$(document).on("click", ".weekProbDetailViewBtn", function(){
		var rowRoot = $(this).parents(".weekProbDiv");
		
		rowRoot.find(".weekProbDetailDiv").toggle();
	});
	
	// 과제 제출
	$(document).on("click", ".weekProbDetailEditBtn", function(){
		location.href = $(this).attr("link");
	});

	// 과제 피드백
	$(document).on("click", ".weekProbFeedbackBtn", function(){
		location.href = $(this).attr("link");
	});
});
