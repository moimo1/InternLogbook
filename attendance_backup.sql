--
-- PostgreSQL database dump
--

\restrict NClsP2cnLHzxRddJCRQkLjEGEazgLfNJr3rK6LW3gGP0DD79Okxsk11VXc06QS5

-- Dumped from database version 15.18
-- Dumped by pg_dump version 15.18

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: approved_overtime; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.approved_overtime (
    id integer NOT NULL,
    user_id integer,
    overtime_date date NOT NULL,
    hours_approved numeric(4,2) NOT NULL
);


ALTER TABLE public.approved_overtime OWNER TO admin;

--
-- Name: approved_overtime_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.approved_overtime_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.approved_overtime_id_seq OWNER TO admin;

--
-- Name: approved_overtime_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.approved_overtime_id_seq OWNED BY public.approved_overtime.id;


--
-- Name: excused_absences; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.excused_absences (
    id integer NOT NULL,
    user_id integer,
    absence_date date NOT NULL,
    reason text DEFAULT 'Excused Absence'::text
);


ALTER TABLE public.excused_absences OWNER TO admin;

--
-- Name: excused_absences_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.excused_absences_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.excused_absences_id_seq OWNER TO admin;

--
-- Name: excused_absences_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.excused_absences_id_seq OWNED BY public.excused_absences.id;


--
-- Name: logs; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.logs (
    id integer NOT NULL,
    user_id integer,
    log_type character varying(10) NOT NULL,
    "timestamp" timestamp without time zone NOT NULL
);


ALTER TABLE public.logs OWNER TO admin;

--
-- Name: logs_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.logs_id_seq OWNER TO admin;

--
-- Name: logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.logs_id_seq OWNED BY public.logs.id;


--
-- Name: system_settings; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.system_settings (
    key character varying(50) NOT NULL,
    value text NOT NULL
);


ALTER TABLE public.system_settings OWNER TO admin;

--
-- Name: users; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    password character varying(255) NOT NULL,
    roles character varying(20) DEFAULT 'intern'::character varying,
    is_active integer DEFAULT 1
);


ALTER TABLE public.users OWNER TO admin;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO admin;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: approved_overtime id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.approved_overtime ALTER COLUMN id SET DEFAULT nextval('public.approved_overtime_id_seq'::regclass);


--
-- Name: excused_absences id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.excused_absences ALTER COLUMN id SET DEFAULT nextval('public.excused_absences_id_seq'::regclass);


--
-- Name: logs id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.logs ALTER COLUMN id SET DEFAULT nextval('public.logs_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: approved_overtime; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.approved_overtime (id, user_id, overtime_date, hours_approved) FROM stdin;
\.


--
-- Data for Name: excused_absences; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.excused_absences (id, user_id, absence_date, reason) FROM stdin;
\.


--
-- Data for Name: logs; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.logs (id, user_id, log_type, "timestamp") FROM stdin;
2	6	IN	2026-07-21 07:00:00
3	5	IN	2026-07-20 07:30:00
4	5	IN	2026-07-20 13:00:00
6	5	OUT	2026-07-20 12:01:00
7	5	OUT	2026-07-20 17:31:00
8	3	IN	2026-07-20 07:00:00
9	3	IN	2026-07-20 13:00:00
10	3	IN	2026-07-21 07:10:00
11	3	OUT	2026-07-20 12:00:00
12	3	OUT	2026-07-20 17:30:00
13	6	IN	2026-07-20 07:00:00
14	6	IN	2026-07-20 13:00:00
15	6	OUT	2026-07-20 12:00:00
16	6	OUT	2026-07-20 17:30:00
17	4	IN	2026-07-20 07:27:00
19	5	IN	2026-07-21 07:30:00
5	5	IN	2026-07-21 01:00:00
20	4	IN	2026-07-21 07:31:00
21	4	OUT	2026-07-20 12:00:00
22	4	OUT	2026-07-20 17:30:00
18	4	IN	2026-07-20 13:00:00
\.


--
-- Data for Name: system_settings; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.system_settings (key, value) FROM stdin;
schedule_rules	{"MWF": {"start": "07:30", "end": "17:30", "break_start": "12:00", "break_end": "13:00"}, "TF": {"start": "07:30", "end": "17:00", "break_start": "12:00", "break_end": "13:00"}}
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.users (id, username, password, roles, is_active) FROM stdin;
1	admin	admin123	admin	1
3	Lance Kenneth Cariaga	lance123	intern	1
4	Whaquin Ferrer	whaquin123	intern	1
5	Caleb Gapuz	caleb123	intern	1
6	Renz Dadpaas	renz123	intern	1
\.


--
-- Name: approved_overtime_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.approved_overtime_id_seq', 1, false);


--
-- Name: excused_absences_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.excused_absences_id_seq', 1, false);


--
-- Name: logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.logs_id_seq', 22, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.users_id_seq', 6, true);


--
-- Name: approved_overtime approved_overtime_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.approved_overtime
    ADD CONSTRAINT approved_overtime_pkey PRIMARY KEY (id);


--
-- Name: approved_overtime approved_overtime_user_id_overtime_date_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.approved_overtime
    ADD CONSTRAINT approved_overtime_user_id_overtime_date_key UNIQUE (user_id, overtime_date);


--
-- Name: excused_absences excused_absences_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.excused_absences
    ADD CONSTRAINT excused_absences_pkey PRIMARY KEY (id);


--
-- Name: excused_absences excused_absences_user_id_absence_date_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.excused_absences
    ADD CONSTRAINT excused_absences_user_id_absence_date_key UNIQUE (user_id, absence_date);


--
-- Name: logs logs_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_pkey PRIMARY KEY (id);


--
-- Name: system_settings system_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.system_settings
    ADD CONSTRAINT system_settings_pkey PRIMARY KEY (key);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: approved_overtime approved_overtime_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.approved_overtime
    ADD CONSTRAINT approved_overtime_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: excused_absences excused_absences_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.excused_absences
    ADD CONSTRAINT excused_absences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: logs logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict NClsP2cnLHzxRddJCRQkLjEGEazgLfNJr3rK6LW3gGP0DD79Okxsk11VXc06QS5

