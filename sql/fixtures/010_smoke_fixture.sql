-- Fixture sintético para verificação automatizada.
--
-- Não são dados do Inep: são poucas ofertas construídas para exercitar a
-- lógica que mais erra em silêncio. Um banco vazio faria as asserções passarem
-- vaziamente, provando apenas que o SQL compila. Com este fixture, as
-- asserções verificam comportamento.
--
-- As tabelas raw são todas TEXT e admitem nulo, então basta preencher as
-- colunas que as views leem.
--
-- Casos cobertos:
--   IES 1 / curso 100  presencial saudável, matrículas estáveis
--   IES 1 / curso 200  presencial cujas matrículas caem à metade
--   IES 1 / curso 400  presencial que desaparece do Censo a partir de 2021
--   IES 2 / curso 300  EAD com capacidade na dimensão 3 e alunos na dimensão 2,
--                      distribuídos em dois municípios para exercitar a soma
--
-- O ano de 2020 usa co_cine_rotulo2, a grafia divergente daquele pacote, para
-- que a normalização da união longitudinal seja exercitada de verdade.

TRUNCATE TABLE raw.censo_superior_cursos_2018;
TRUNCATE TABLE raw.censo_superior_cursos_2019;
TRUNCATE TABLE raw.censo_superior_cursos_2020;
TRUNCATE TABLE raw.censo_superior_cursos_2021;
TRUNCATE TABLE raw.censo_superior_cursos_2022;
TRUNCATE TABLE raw.censo_superior_cursos_2023;
TRUNCATE TABLE raw.censo_superior_cursos_2024;
TRUNCATE TABLE raw.censo_superior_ies_2018;
TRUNCATE TABLE raw.censo_superior_ies_2024;

-- Presencial: dimensão 1 carrega capacidade e alunos na mesma linha.
INSERT INTO raw.censo_superior_cursos_2018 (
    nu_ano_censo, tp_dimensao, co_regiao, co_uf, co_municipio, co_ies,
    co_curso, no_curso, co_cine_rotulo, no_cine_rotulo,
    tp_modalidade_ensino, tp_nivel_academico, tp_grau_academico,
    tp_rede, tp_categoria_administrativa, tp_organizacao_academica,
    qt_curso, qt_vg_total, qt_inscrito_total, qt_ing, qt_mat, qt_conc
) VALUES
    ('2018','1','3','35','3550308','1','100','Saudavel','0100','Rotulo A',
     '1','1','1','2','4','1','1','100','200','80','400','50'),
    ('2018','1','3','35','3550308','1','200','Declinante','0200','Rotulo B',
     '1','1','1','2','4','1','1','200','100','40','300','40'),
    ('2018','1','3','35','3550308','1','400','Encerrada','0400','Rotulo D',
     '1','1','1','2','4','1','1','150','60','20','200','30');

INSERT INTO raw.censo_superior_cursos_2019 (
    nu_ano_censo, tp_dimensao, co_regiao, co_uf, co_municipio, co_ies,
    co_curso, no_curso, co_cine_rotulo, no_cine_rotulo,
    tp_modalidade_ensino, tp_nivel_academico, tp_grau_academico,
    tp_rede, tp_categoria_administrativa, tp_organizacao_academica,
    qt_curso, qt_vg_total, qt_inscrito_total, qt_ing, qt_mat, qt_conc
) VALUES
    ('2019','1','3','35','3550308','1','100','Saudavel','0100','Rotulo A',
     '1','1','1','2','4','1','1','100','210','85','410','55'),
    ('2019','1','3','35','3550308','1','200','Declinante','0200','Rotulo B',
     '1','1','1','2','4','1','1','200','90','35','280','45'),
    ('2019','1','3','35','3550308','1','400','Encerrada','0400','Rotulo D',
     '1','1','1','2','4','1','1','150','40','12','150','60');

-- 2020 usa a grafia divergente co_cine_rotulo2.
INSERT INTO raw.censo_superior_cursos_2020 (
    nu_ano_censo, tp_dimensao, co_regiao, co_uf, co_municipio, co_ies,
    co_curso, no_curso, co_cine_rotulo2, no_cine_rotulo,
    tp_modalidade_ensino, tp_nivel_academico, tp_grau_academico,
    tp_rede, tp_categoria_administrativa, tp_organizacao_academica,
    qt_curso, qt_vg_total, qt_inscrito_total, qt_ing, qt_mat, qt_conc
) VALUES
    ('2020','1','3','35','3550308','1','100','Saudavel','0100','Rotulo A',
     '1','1','1','2','4','1','1','100','220','90','420','60'),
    ('2020','1','3','35','3550308','1','200','Declinante','0200','Rotulo B',
     '1','1','1','2','4','1','1','200','80','30','260','50'),
    ('2020','1','3','35','3550308','1','400','Encerrada','0400','Rotulo D',
     '1','1','1','2','4','1','1','150','20','5','100','80');

-- A partir de 2021 o curso 400 desaparece: o rótulo de 2019 e de 2020 deve
-- marcar deterioração por desaparecimento.
INSERT INTO raw.censo_superior_cursos_2021 (
    nu_ano_censo, tp_dimensao, co_regiao, co_uf, co_municipio, co_ies,
    co_curso, no_curso, co_cine_rotulo, no_cine_rotulo,
    tp_modalidade_ensino, tp_nivel_academico, tp_grau_academico,
    tp_rede, tp_categoria_administrativa, tp_organizacao_academica,
    qt_curso, qt_vg_total, qt_inscrito_total, qt_ing, qt_mat, qt_conc
) VALUES
    ('2021','1','3','35','3550308','1','100','Saudavel','0100','Rotulo A',
     '1','1','1','2','4','1','1','100','230','95','430','62'),
    ('2021','1','3','35','3550308','1','200','Declinante','0200','Rotulo B',
     '1','1','1','2','4','1','1','200','70','25','200','55');

INSERT INTO raw.censo_superior_cursos_2022 (
    nu_ano_censo, tp_dimensao, co_regiao, co_uf, co_municipio, co_ies,
    co_curso, no_curso, co_cine_rotulo, no_cine_rotulo,
    tp_modalidade_ensino, tp_nivel_academico, tp_grau_academico,
    tp_rede, tp_categoria_administrativa, tp_organizacao_academica,
    qt_curso, qt_vg_total, qt_inscrito_total, qt_ing, qt_mat, qt_conc
) VALUES
    ('2022','1','3','35','3550308','1','100','Saudavel','0100','Rotulo A',
     '1','1','1','2','4','1','1','100','240','100','440','65'),
    -- Matrículas em 120 contra 260 em 2020: menos de metade, logo o rótulo de
    -- 2020 para esta oferta é deterioração.
    ('2022','1','3','35','3550308','1','200','Declinante','0200','Rotulo B',
     '1','1','1','2','4','1','1','200','60','20','120','60');

INSERT INTO raw.censo_superior_cursos_2023 (
    nu_ano_censo, tp_dimensao, co_regiao, co_uf, co_municipio, co_ies,
    co_curso, no_curso, co_cine_rotulo, no_cine_rotulo,
    tp_modalidade_ensino, tp_nivel_academico, tp_grau_academico,
    tp_rede, tp_categoria_administrativa, tp_organizacao_academica,
    qt_curso, qt_vg_total, qt_inscrito_total, qt_ing, qt_mat, qt_conc
) VALUES
    ('2023','1','3','35','3550308','1','100','Saudavel','0100','Rotulo A',
     '1','1','1','2','4','1','1','100','250','105','450','67');

-- EAD em 2024: a capacidade vem da dimensão 3 em nível nacional e os alunos
-- da dimensão 2 por município. Somar as duas dimensões produziria dupla
-- contagem, e é justamente o que a reconciliação evita.
INSERT INTO raw.censo_superior_cursos_2024 (
    nu_ano_censo, tp_dimensao, co_regiao, co_uf, co_municipio, co_ies,
    co_curso, no_curso, co_cine_rotulo, no_cine_rotulo,
    tp_modalidade_ensino, tp_nivel_academico, tp_grau_academico,
    tp_rede, tp_categoria_administrativa, tp_organizacao_academica,
    qt_curso, qt_vg_total, qt_inscrito_total, qt_ing, qt_mat, qt_conc
) VALUES
    ('2024','1','3','35','3550308','1','100','Saudavel','0100','Rotulo A',
     '1','1','1','2','4','1','1','100','260','110','460','70'),
    ('2024','3','3',NULL,NULL,'2','300','Ead Nacional','0300','Rotulo C',
     '2','1','1','2','5','1','1','5000','1200','0','0','0'),
    ('2024','2','3','35','3550308','2','300','Ead Nacional','0300','Rotulo C',
     '2','1','1','2','5','1','0','0','0','300','900','100'),
    ('2024','2','2','29','2927408','2','300','Ead Nacional','0300','Rotulo C',
     '2','1','1','2','5','1','0','0','0','200','600','50'),
    -- Dimensão 4 é oferta no exterior e precisa ficar fora do recorte.
    ('2024','4','3',NULL,NULL,'2','300','Ead Nacional','0300','Rotulo C',
     '2','1','1','2','5','1','1','999','999','999','999','999');

INSERT INTO raw.censo_superior_ies_2024 (
    nu_ano_censo, co_ies, no_ies, sg_ies, tp_organizacao_academica,
    tp_categoria_administrativa, co_municipio_ies, sg_uf_ies, tp_rede
) VALUES
    ('2024','1','Instituicao Um','IU1','1','4','3550308','SP','2'),
    ('2024','2','Instituicao Dois','ID2','1','5','2927408','BA','2');

INSERT INTO raw.censo_superior_ies_2018 (
    nu_ano_censo, co_ies, no_ies, sg_ies, tp_organizacao_academica,
    tp_categoria_administrativa, co_municipio_ies, sg_uf_ies
) VALUES
    ('2018','1','Instituicao Um','IU1','1','4','3550308','SP');
