![dbimage](https://github.com/Ewha-Project-T/backend/blob/main/user%20table.png?raw=true)


```create table user(user_no int primary key auto_increment, email char(50) not null unique,password varchar(250), name char(50) not null ,major char(50) not null ,permission int default 1, login_fail_limit int default 0, lecture_no int , foreign key(lecture_no) references lecture(lecture_no) on delete cascade);```


```create table lecture(lecture_no int primary key auto_increment, lecture_name varchar(50) not null,year char(7) not null,semester char(10) not null,major char(50) not null, separated char(5) not null,boss varchar(50) not null);```
