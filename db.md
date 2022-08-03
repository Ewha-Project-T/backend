![Uploading user table.png…]()
create table user(user_no int primary key auto_increment, email char(50) not null unique,password varchar(250), name char(100) not null ,permission int default 1, login_fail_limit int default 0, lecture_no int , foreign key(lecture_no) references project(lecture_no) on delete cascade);
