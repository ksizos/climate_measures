@extends('layouts.app')

@section('title', 'Климатический консультант')


@push('styles')
<link
    rel="stylesheet"
    href="{{ asset('css/climate/index.css') }}">
@endpush


@section('content')

<div class="climate-app">

    @include('components.climate.sidebar', [
    'conversations' => $conversations
    ])

    <main class="climate-main">

        @include('components.climate.header')

        <section class="climate-content">

            @include('components.climate.welcome')

            @include('components.climate.messages')

        </section>

        @include('components.climate.composer')

    </main>

</div>

@endsection


@push('scripts')
<script
    type="module"
    src="{{ asset('js/climate/index.js') }}">
</script>
@endpush
