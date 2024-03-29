$(document).ready(function(){
	// 오류 메시지 출력
	if($("#serverMsg").text() != "" && $("#serverMsg").text() != undefined){
		alert($("#serverMsg").text()); 
	}
	// 회원가입 이메일 중복 체크
	$(document).on("change", "input[name=email]", function(){
		var email = $(this).val();
		$.ajax({
			url:"/join",
			data:{mode:"emailChk",email:email},
			method:"GET",
            dataType:"json",
		})
		.done(function(data, textStatus, xhr) {
			$(".email .comment").text("이메일 중복");
			$(".email .comment").show();
			$("input[name=emailFlag]").val("F");
		})
		.fail(function(data,textStatus,errorThrown){
			$(".email .comment").hide();
			$("input[name=emailFlag]").val("T");
		})
	});
	
	// 비밀번호 재확인
	$(document).on("change", "input[name=pw], input[name=pw2]", function(){
		var passwd = $("input[name=pw]").val();
		var passwdChk = $("input[name=pw2]").val();
		
		if(passwd != "" && passwd != passwdChk){
			$(".passwdChk .comment").text("비밀번호 확인");
			$(".passwdChk .comment").show();
			$("input[name=passwdFlag]").val("F");
		}else{
			$(".passwdChk .comment").hide();
			$("input[name=passwdFlag]").val("T");
		}
	});
	
	// 회원가입 취소
	$(document).on("click", ".btn-cancel", function(){
		history.back();
	});
/*
	$("#login").click(function() {//로그인
		var action = $("#form1").attr('action');

		var form_data = {
			email: $("#email").val(),
			pw: $("#pw").val(),
		};
		$.ajax({
			type: "POST",
			url: action,
			data: form_data,
			dataType:"json"
		})
		.done(function(data, textStatus, xhr) {
			console.log(data);
			console.log(textStatus);
			console.log(JSON.stringify(xhr));
			alert(xhr);
				if(data == 'success') {
					alert("로그인 성공");
				}
				else {
					alert("아이디 또는 비밀번호가 잘못되었습니다");	
				}
		})		
	});
*/
});

function loginFormCheck(){
	var email = $("input[name=email]");
	var passwd = $("input[name=pw]");
	
	if(email.val() == ""){
		email.focus();
		$(".email .error-txt").show();
		return false;
	}else{
		$(".email .error-txt").hide();
	}
	if(passwd.val() == ""){
		passwd.focus();
		$(".password .error-txt").show();
		return false;
	}else{
		$(".password .error-txt").hide();
	}
	
	return true;
}

function joinFormCheck(){
	var email = $("input[name=email]");
	var passwd = $("input[name=pw]");
	var passwdChk = $("input[name=pw2]");
	var name = $("input[name=name]");
	var dp = $("select[name=major]");
	var type = $("select[name=perm]");
	var emailFlag = $("input[name=emailFlag]");
	var passwdFlag = $("input[name=passwdFlag]");
	
	if(email.val() == ""){
		email.focus();
		$(".email .comment").text("이메일 확인");
		$(".email .comment").show();
		return false;
	}else if(emailFlag.val() == "F"){
		return false;
	}else{
		$(".email .comment").hide();
	}
	if(passwd.val() == ""){
		passwd.focus();
		$(".passwd .comment").text("비밀번호 확인");
		$(".passwd .comment").show();
		return false;
	}else{
		$(".passwd .comment").hide();
	}
	if(passwdChk.val() == ""){
		passwdChk.focus();
		$(".passwdChk .comment").text("비밀번호 확인");
		$(".passwdChk .comment").show();
		return false;
	}else if(passwdFlag.val() == "F"){
		return false;
	}else{
		$(".passwdChk .comment").hide();
	}
	if(name.val() == ""){
		name.focus();
		$(".name .comment").text("이름 확인");
		$(".name .comment").show();
		return false;
	}else{
		$(".name .comment").hide();
	}
	if(dp.val() == ""){
		dp.focus();
		$(".dp .comment").text("학과 확인");
		$(".dp .comment").show();
		return false;
	}else{
		$(".dp .comment").hide();
	}
	if(type.val() == ""){
		type.focus();
		$(".type .comment").text("분류 확인");
		$(".type .comment").show();
		return false;
	}else{
		$(".type .comment").hide();
	}
	
	return true;
}
