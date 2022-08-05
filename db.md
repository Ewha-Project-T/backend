![dbimage](https://github.com/Ewha-Project-T/backend/blob/main/db_table.png?raw=true)


```create table user(user_no int primary key auto_increment, email char(50) not null unique,password varchar(250) not null, name char(50) not null ,major char(50) not null ,permission int default 1, login_fail_limit int default 0, access_check int default 0);```   


```create table lecture(lecture_no int primary key auto_increment, lecture_name varchar(50) not null,year char(7) not null,semester char(30) not null,major char(50) not null, separated char(20) not null,boss varchar(50) not null);```   

```create table member(member_no int primary key auto_increment, user_no int,lecture_no int,permission int default 1,foreign key(user_no) references user(user_no) on delete cascade,foreign key(lecture_no) references lecture(lecture_no) on delete cascade);```   

```create table homework(homework_no int primary key auto_increment, lecture_no int,foreign key(lecture_no) references lecture(lecture_no) on delete cascade);```   

```create table homework_check(check_no int primary key auto_increment, homework_no int,member_no int,homework_check int default 0,foreign key(homework_no) references homework(homework_no) on delete cascade,foreign key(member_no) references member(member_no) on delete cascade);```   
