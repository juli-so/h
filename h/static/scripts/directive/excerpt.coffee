module.exports = [ '$timeout', ($timeout) ->
    link: (scope, elem, attr, ctrl) ->
      $timeout -> if elem[0].scrollHeight > elem[0].clientHeight
        elem.prepend angular.element '<span class="more-quote"> More...</span>'
        elem.append angular.element '<span class="less-quote"> Less ^</span>'
        elem.find('.more-quote').on 'click', ->
          $(this).hide()
          elem.addClass('show-full-quote')
        elem.find('.less-quote').on 'click', ->
          elem.find('.more-quote').show()
          elem.removeClass('show-full-quote')
    restrict: 'A'
    scope: {}
]
