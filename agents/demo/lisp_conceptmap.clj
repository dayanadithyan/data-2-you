(defpackage :dota-query-generator
  (:use :cl))

(in-package :dota-query-generator)

;; Generate GraphQL queries for hero performance
(defmacro generate-hero-performance-query (hero-id &key (patches nil) (time-resolution "PATCH"))
  "Generate a GraphQL query for hero performance analysis"
  `(format nil "
    query HeroPerformance {
      hero(id: ~A) {
        name
        displayName
        timeline(resolution: ~A~A) {
          timestamp
          winRate
          pickRate
          banRate
          averageGPM
          averageXPM
          ~@[itemBuilds { items { id name } frequency winRate }~]
        }
      }
    }"
    ,hero-id
    ,time-resolution
    ,(if patches
         (format nil ", patches: [~{\"~A\"~^, ~}]" patches)
         "")
    ,(if (eq time-resolution "PATCH") t nil)))

;; Define rule-based system for strategy classification
(defun classify-strategy (match-data)
  "Classify team strategy based on match data"
  (let ((early-kills (getf match-data :kills-before-10min))
        (lane-distribution (getf match-data :lane-distribution))
        (first-objective (getf match-data :first-objective))
        (avg-item-timing (getf match-data :avg-item-timing)))
    
    (cond
      ;; Early aggression strategy
      ((> early-kills 10)
       (if (eq first-objective :tower)
           :push-strategy
           :gank-strategy))
      
      ;; Split-push strategy
      ((every #'(lambda (lane) (< lane 0.5)) lane-distribution)
       :split-push-strategy)
      
      ;; Late-game strategy
      ((> avg-item-timing 25)
       :late-game-strategy)
      
      ;; Default
      (t :balanced-strategy))))

;; Integration with Python using cl4py
(defun example-python-integration ()
  "Example of how this would be called from Python"
  (format t "
# Python code:
from cl4py import Lisp

lisp = Lisp()
query = lisp.eval(\"(dota-query-generator:generate-hero-performance-query 1 :patches '(\\\"7.20\\\" \\\"7.21\\\") :time-resolution \\\"MONTH\\\")\")

# Execute GraphQL query using the generated string
result = execute_graphql(query)
"))