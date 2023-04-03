GRANT ALL PRIVILEGES ON DATABASE zhk_db TO zhk_meetings;

INSERT INTO "zhk_meetings_app_cooperativequestion" (question, is_available_for_regular_meeting, 
is_available_for_intramural_meeting, is_available_for_extramural_meeting)
VALUES ('Утверждение устава кооператива', TRUE, TRUE, FALSE),
('Внесение изменений в устав кооператива', TRUE, TRUE, FALSE),
('Утверждение устава кооператива в новой редакции', TRUE, TRUE, FALSE),
('Утверждение внутренних документов кооператива, регулирующих деятельность органов управления '
            'кооператива и иных органов кооператива, предусмотренных настоящим уставом', 
            TRUE, TRUE, TRUE),
('Утверждение размера паевого фонда кооператива и порядка его использования кооперативом', 
            TRUE, TRUE, TRUE),
('Принятие решения о ликвидации кооператива, а также назначение ликвидационной комиссии и '
            'утверждение промежуточного и окончательного ликвидационных балансов', 
            TRUE, TRUE, FALSE),
('Установление размера обязательных взносов членов кооператива, за исключением размера '
            'вступительных и паевых взносов, определяемых настоящим уставом', 
            TRUE, TRUE, TRUE),
('Избрание правления кооператива', TRUE, FALSE, FALSE),
('Прекращение полномочий правления кооператива', TRUE, TRUE, TRUE),
('Избрание ревизионной комиссии (ревизора)', TRUE, TRUE, FALSE),
('Прекращение, в том числе досрочное, полномочий ревизионной комиссии (ревизора) '
            'кооператива или ее отдельных членов', TRUE, TRUE, TRUE),
('Утверждение отчетов о деятельности правления кооператива', TRUE, FALSE, FALSE),
('Утверждение отчета о деятельности ревизионной комиссии (ревизора) кооператива', 
            TRUE, FALSE, FALSE),
('Утверждение аудиторского заключения о достоверности бухгалтерской (финансовой) отчетности '
            'кооператива по итогам финансового года', TRUE, TRUE, TRUE),
('Утверждение заключений ревизионной комиссии (ревизора) кооператива по результатам проверки '
            'финансово-хозяйственной деятельности кооператива', TRUE, TRUE, TRUE),
('Утверждение отчетов об использовании фондов кооператива', TRUE, TRUE, TRUE),
('Принятие решения об исключении граждан из кооператива', TRUE, TRUE, FALSE),
('Определение порядка формирования фондов кооператива, за исключением паевого фонда ' 
            'кооператива, и их использования', TRUE, TRUE, TRUE)
ON CONFLICT (questions) DO NOTHING;


INSERT INTO "zhk_meetings_app_cooperativequestion" (question, is_clickable, is_available_for_regular_meeting, 
is_available_for_intramural_meeting, is_available_for_extramural_meeting)
VALUES ('Принятие решения о реорганизации кооператива', TRUE, TRUE, TRUE, FALSE),
('Прекращение полномочий отдельных членов правления', TRUE, TRUE, TRUE, TRUE),
('Принятие решения о приеме граждан в члены кооператива', TRUE, TRUE, TRUE, FALSE)
ON CONFLICT (questions) DO NOTHING;


INSERT INTO "zhk_meetings_app_cooperativequestion" (question, is_report_approval, is_clickable, 
is_available_for_regular_meeting, is_available_for_intramural_meeting, 
is_available_for_extramural_meeting)
VALUES ('Утверждение годового отчета кооператива и годовой бухгалтерской (финансовой) '
            'отчетности кооператива', TRUE, TRUE, TRUE, FALSE, FALSE)
ON CONFLICT (questions) DO NOTHING;
