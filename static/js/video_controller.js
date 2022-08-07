var exampleAudioPlayer;
var submitAudioPlayer;
var fd;
$(document).ready(function(){
	// 원음
	const sampleAudioOptions = {
		controls: true,
		autoplay: false,
		fluid: false,
		bigPlayButton: false,
		plugins: {
			wavesurfer: {
				backend: 'MediaElement',
				displayMilliseconds: false,
				debug: true,
				waveColor: '#086280',
				progressColor: 'black',
				cursorColor: 'black',
				hideScrollbar: true
			}
		}
	};
	exampleAudioPlayer = videojs('exampleAudioWaveSurfer', sampleAudioOptions, function() {
		exampleAudioPlayer.src({src: 'audio/audio_sample.wav', type: 'audio/wav'});
	});
	
	exampleAudioPlayer.on("ended", function(){
		// 동시통역
		if($(".simultaneousBtn").length > 0){
			var btnEle = $(".sequentialBtn");
			exampleAudioPlayer.pause();
			exampleAudioPlayer.currentTime(0)
			submitAudioPlayer.record().stop();
			btnEle.removeClass("recoding");
			btnEle.text("통역시작");
		}
	});
	
	// 과제음
	const assignmentAudioOptions = {
		controls: true,
		autoplay: false,
		fluid: false,
		bigPlayButton: false,
		plugins: {
			wavesurfer: {
				backend: 'MediaElement',
				displayMilliseconds: false,
				debug: true,
				waveColor: '#086280',
				progressColor: 'black',
				cursorColor: 'black',
				hideScrollbar: true
			}
		}
	};
	assignmentAudioPlayer = videojs('assignmentAudioWaveSurfer', assignmentAudioOptions, function() {
		assignmentAudioPlayer.src({src: 'audio/audio_sample.wav', type: 'audio/wav'});
	});
	
	assignmentAudioPlayer.on("ended", function(){
	});
	
	// 녹음
	var submitAudioOptions = {
		controls: true,
		bigPlayButton: false,
		fluid: false,
		plugins: {
			wavesurfer: {
				backend: 'WebAudio',
				waveColor: '#6fffe9',
				progressColor: 'black',
				displayMilliseconds: true,
				debug: true,
				cursorWidth: 1,
				hideScrollbar: true,
				plugins: [
					WaveSurfer.microphone.create({
						bufferSize: 4096,
						numberOfInputChannels: 1,
						numberOfOutputChannels: 1,
						constraints: {
							video: false,
							audio: true
						}
					})
				]
			},
			record: {
				audio: true,
				video: false,
				maxLength: 600,
				displayMilliseconds: true,
				debug: true,
				audioEngine: 'recorder.js'
			}
		}
	};
	submitAudioPlayer = videojs('submitAudioWaveSurfer', submitAudioOptions, function() {
	});
	
	submitAudioPlayer.on('ready', function(){
		submitAudioPlayer.record().getDevice();
	});

	submitAudioPlayer.on('deviceError', function() {
		console.log('device error:', submitAudioPlayer.deviceErrorCode);
	});

	submitAudioPlayer.on('error', function(element, error) {
		console.error(error);
	});

	submitAudioPlayer.on('startRecord', function() {
		console.log('started recording!');
	});

	submitAudioPlayer.on('finishRecord', function() {
		console.log('finished recording: ', submitAudioPlayer.recordedData);
	});
	
	// 동시 통역
	$(document).on("click", ".simultaneousBtn", function(){
		var btnEle = $(this);
		
		if(!btnEle.hasClass("recoding")){
			// 녹음시작
			exampleAudioPlayer.play();
			submitAudioPlayer.record().start();
			btnEle.addClass("recoding");
			btnEle.text("녹음중/취소");
		}else{
			// 녹음아님
			exampleAudioPlayer.pause();
			exampleAudioPlayer.currentTime(0)
			submitAudioPlayer.record().stop();
			btnEle.removeClass("recoding");
			btnEle.text("통역시작");
		}
	});
	
	// 녹음본 제출
	$(document).on("click", ".submitRecordDataBtn", function(){
		// 녹음 데이터 보내기
		fd = new FormData();
		fd.append('assignment', '123');
		fd.append('wav', submitAudioPlayer.recordedData);
		$.ajax({
			url: "https://ewha.ltra.cc/stt",
			type: "PUT",
			data: fd,
			processData: false,
			contentType: false
		}).done(function(data){
			console.log(data);
		});
	});
});