$(document).ready(function(){
	// 로그아웃 버튼
	$(document).on("click", ".logout", function(){
		location.href = "./index.html";
	});
	
	// 취소버튼
	$(document).on("click", ".btn-cancel", function(){
		history.back();
	});

	// 링크이동
	$(document).on("click", ".link", function(){
		location.href = $(this).attr("link");
	});

	// 강의만들기 수강생 팝업
	$(document).on("click", ".userList", function(){
		$(".userListPopDiv").show();
	});

	// 강의만들기 수강생 팝업 줄 클릭
	$(document).on("click", ".userListPopDiv li", function(){
		var ele = $(this).find("input[type=checkbox]");
		if(ele.is(':checked')){
			ele.prop("checked", false);
			$(this).removeClass("checked");
		}else{
			ele.prop("checked", true);
			$(this).addClass("checked");
		}
	});

	// 강의만들기 수강생 팝업 닫기
	$(document).on("click", ".btn-popClose", function(){
		$(".userListPopDiv").hide();
	});

	// 강의만들기 수강생 선택완료
	$(document).on("click", ".btn-popSelect", function(){
		var eleList = $(".userListPopDiv").find("li.checked").clone();
		$(".userList").empty();
		$(".userList").append(eleList);
		$(".userListPopDiv").hide();
	});
	
	// 과제목록 상세보기
	$(document).on("click", ".weekProbDetailViewBtn", function(){
		var rowRoot = $(this).parents(".weekProbDiv");
		
		rowRoot.find(".weekProbDetailDiv").toggle();
	});
	
	// 과제 피드백
	$(document).on("click", ".weekProbFeedbackBtn", function(){
		location.href = $(".weekProbFeedbackBtn").attr("link");
	});
	//과제 제출
	$(document).on("click", ".weekProbDetailEditBtn", function(){
		location.href = $(this).attr("link");
	 });

});
