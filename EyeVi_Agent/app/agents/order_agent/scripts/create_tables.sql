create table products
(
    _id           bigint         not null
        primary key,
    name          varchar(255)   not null,
    description   text           null,
    brand         varchar(255)   null,
    category      varchar(100)   null,
    gender        varchar(20)    null,
    weight        varchar(20)    null,
    quantity      int            null,
    images        json           null,
    rating        float          null,
    newPrice      decimal(15, 2) null,
    trending      tinyint(1)     null,
    frameMaterial varchar(100)   null,
    lensMaterial  varchar(100)   null,
    lensFeatures  varchar(100)   null,
    frameShape    varchar(50)    null,
    lensWidth     varchar(10)    null,
    bridgeWidth   varchar(10)    null,
    templeLength  varchar(10)    null,
    color         varchar(50)    null,
    availability  varchar(20)    null,
    price         decimal(15, 2) not null,
    image         varchar(255)   null,
    stock         int default 0  null
);

create table users
(
    id                bigint unsigned auto_increment
        primary key,
    name              varchar(255)                         not null,
    email             varchar(255)                         not null,
    password          varchar(255)                         not null,
    is_admin          tinyint(1) default 0                 null,
    email_verified_at timestamp                            null,
    created_at        timestamp  default CURRENT_TIMESTAMP null,
    updated_at        timestamp  default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP,
    constraint email
        unique (email),
    constraint users_pk
        unique (email)
);

create table addresses
(
    id         bigint unsigned auto_increment
        primary key,
    user_id    bigint unsigned                      not null,
    name       varchar(255)                         not null,
    phone      varchar(20)                          not null,
    address    text                                 not null,
    city       varchar(100)                         not null,
    state      varchar(100)                         null,
    country    varchar(100)                         not null,
    is_default tinyint(1) default 0                 null,
    created_at timestamp  default CURRENT_TIMESTAMP null,
    updated_at timestamp  default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP,
    constraint addresses_ibfk_1
        foreign key (user_id) references users (id)
            on delete cascade
);

create index user_id
    on addresses (user_id);

create table carts
(
    id         bigint unsigned auto_increment
        primary key,
    user_id    bigint unsigned                     not null,
    created_at timestamp default CURRENT_TIMESTAMP null,
    updated_at timestamp default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP,
    constraint carts_ibfk_1
        foreign key (user_id) references users (id)
            on delete cascade
);

create table cart_details
(
    id         bigint unsigned auto_increment
        primary key,
    cart_id    bigint unsigned                     not null,
    product_id varchar(36)                         not null,
    quantity   int       default 1                 null,
    created_at timestamp default CURRENT_TIMESTAMP null,
    updated_at timestamp default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP,
    constraint cart_details_ibfk_1
        foreign key (cart_id) references carts (id)
            on delete cascade
);

create index cart_id
    on cart_details (cart_id);

create index product_id
    on cart_details (product_id);

create index user_id
    on carts (user_id);

create table invoices
(
    id             bigint unsigned auto_increment
        primary key,
    user_id        bigint unsigned                       not null,
    address_id     bigint unsigned                       not null,
    total_items    int                                   not null,
    actual_price   decimal(10, 2)                        not null,
    total_price    decimal(10, 2)                        not null,
    payment_method varchar(50)                           not null,
    payment_status varchar(50) default 'pending'         null,
    order_status   varchar(50) default 'processing'      null,
    created_at     timestamp   default CURRENT_TIMESTAMP null,
    updated_at     timestamp   default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP,
    constraint invoices_ibfk_1
        foreign key (user_id) references users (id),
    constraint invoices_ibfk_2
        foreign key (address_id) references addresses (id)
);

create table invoice_details
(
    id         bigint unsigned auto_increment
        primary key,
    invoice_id bigint unsigned                     not null,
    product_id varchar(36)                         not null,
    quantity   int                                 not null,
    price      decimal(10, 2)                      not null,
    created_at timestamp default CURRENT_TIMESTAMP null,
    updated_at timestamp default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP,
    constraint invoice_details_ibfk_1
        foreign key (invoice_id) references invoices (id)
);

create index invoice_id
    on invoice_details (invoice_id);

create index product_id
    on invoice_details (product_id);

create index address_id
    on invoices (address_id);

create index user_id
    on invoices (user_id);

create table wishlist
(
    id         bigint unsigned auto_increment
        primary key,
    user_id    bigint unsigned                     not null,
    created_at timestamp default CURRENT_TIMESTAMP null,
    updated_at timestamp default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP,
    constraint wishlist_ibfk_1
        foreign key (user_id) references users (id)
            on delete cascade
);

create index user_id
    on wishlist (user_id);

create table wishlist_details
(
    id          bigint unsigned auto_increment
        primary key,
    wishlist_id bigint unsigned                     not null,
    product_id  varchar(36)                         not null,
    created_at  timestamp default CURRENT_TIMESTAMP null,
    updated_at  timestamp default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP,
    constraint wishlist_details_ibfk_1
        foreign key (wishlist_id) references wishlist (id)
            on delete cascade
);

create index product_id
    on wishlist_details (product_id);

create index wishlist_id
    on wishlist_details (wishlist_id);

