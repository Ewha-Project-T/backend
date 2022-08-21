![dbimage](https://github.com/Ewha-Project-T/backend/blob/main/db_table.png?raw=true)


```create table user(user_no int primary key auto_increment, email char(50) not null unique,password varchar(250) not null, name char(50) not null ,major char(50) not null ,permission int default 1, login_fail_limit int default 0, access_check int default 0);```   


```create table lecture(lecture_no int primary key auto_increment, lecture_name varchar(50) not null,year char(7) not null,semester char(30) not null,major char(50) not null, separated char(20) not null,professor varchar(50) not null);```   

```create table attendee(attendee_no int primary key auto_increment, user_no int,lecture_no int,permission int default 1,foreign key(user_no) references user(user_no) on delete cascade,foreign key(lecture_no) references lecture(lecture_no) on delete cascade);```   

```create table assignment(assignment_no int primary key auto_increment, lecture_no int,week varchar(20) not null,limit_time DATETIME not null,as_name varchar(50) not null,as_type varchar(10),keyword TEXT,description TEXT,re_limit varchar(10) not null,speed float not null,disclosure int default 0,original_text TEXT,upload_url varchar(100),foreign key(lecture_no) references lecture(lecture_no) on delete cascade);```   

```create table assignment_check(check_no int primary key auto_increment, assignment_no int,attendee_no int,assignment_check int default 0,foreign key(assignment_no) references assignment(assignment_no) on delete cascade,foreign key(attendee_no) references attendee(attendee_no) on delete cascade);```   

```create table STT(stt_no int primary key auto_increment,user_no int,assignment_no int,wav_file varchar(36),foreign key(user_no) references user(user_no) on delete cascade,foreign key(assignment_no) references assignment(assignment_no) on delete cascade);```

```create table prob_region(region_no int primary key auto_increment,assignment_no int,region_index varchar(10),start varchar(10),end varchar(10),foreign key(assignment_no) references ASSIGNMENT(assignment_no) on delete cascade)```