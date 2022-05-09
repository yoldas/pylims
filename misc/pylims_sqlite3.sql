-- Customer samples. Sanger ID service is implemented as autoincrement.
create table sample (
    customer text not null, -- customer name
    name text not null, -- sample name customer uses
    sample_id integer primary key autoincrement, --unique across all samples
    tag text, -- tag appended default null
    concentration integer,
    unique(customer, name)  -- name is unique across samples from customer
);

-- Sample tubes contain customer sample.
create table sample_tube (
    barcode text primary key,   -- unique tube barcode
    sample_id integer,
    moved_to text,  -- sample moved to barcode
    foreign key(sample_id) references sample(sample_id)  -- holds sample
);

-- Samples are added to lab tubes.
create table lab_tube (
    barcode text primary key,   -- unique plate barcode
    sample_id integer,
    moved_to text,  -- sample moved to barcode
    foreign key(sample_id) references sample(sample_id)  -- adds sample
);

-- Samples are added to plate wells.
create table plate (
    barcode text primary key,
    grid text default '8x12'
);

-- Wells are arranged in a grid on plates.
create table well (
    plate_barcode text not null,
    label text not null, -- A1, A2, ..., H12
    sample_id integer,
    unique (plate_barcode, label),
    foreign key(plate_barcode) references plate(barcode)
    foreign key(sample_id) references sample(sample_id)
);
