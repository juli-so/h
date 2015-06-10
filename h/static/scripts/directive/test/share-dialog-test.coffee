{module, inject} = require('angular-mock')

assert = chai.assert

describe 'share-dialog', ->
  fakeCrossFrame = null
  $scope = null
  $compile = null
  $element = null
  $shareDialog = null
  $timeout = null
  $isolateScope = null

  before ->
    angular.module('h', [])
    .directive('share-dialog', require('../share-dialog'))

  beforeEach module('h')
  beforeEach module('h.templates')

  beforeEach module ($provide) ->
    fakeCrossFrame = {providers: []}
    
    $provide.value 'crossframe', fakeCrossFrame
    return

  beforeEach inject (_$compile_, _$rootScope_, _$timeout_) ->
    $compile = _$compile_
    $timeout = _$timeout_
    $scope = _$rootScope_.$new()

  it 'generates new via link', ->
    $scope.viaPageLink = ''
    fakeCrossFrame.providers.push {entities: ['http://example.com']}
    $element = angular.element('<div share-dialog="">')
    $compile($element)($scope)
    $scope.$digest()
    $isolateScope = $element.isolateScope()
    console.log $isolateScope.viaPageLink
